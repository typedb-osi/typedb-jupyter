import math
import typedb.client
from typedb.api.connection.session import SessionType
from typedb.api.connection.transaction import TransactionType
from typedb.common.exception import TypeDBClientException
from typedb.concept.answer.concept_map import ConceptMap
from typedb.concept.answer.concept_map_group import ConceptMapGroup
from typedb.concept.answer.numeric import Numeric
from typedb.concept.answer.numeric_group import NumericGroup
from tql.exception import ArgumentError, QueryParsingError


def group_key(concept):
    if concept.is_type():
        return str(concept.as_type().get_label())
    elif concept.is_entity():
        return concept.as_entity().get_iid()
    elif concept.is_relation():
        return concept.as_relation().get_iid()
    elif concept.is_attribute():
        return concept.as_attribute().get_value()
    else:
        raise ValueError("Unknown concept type. Please report this error.")


def decode(answer, answer_type):
    if answer_type is ConceptMap:
        return [concept_map.to_json() for concept_map in answer]
    elif answer_type is ConceptMapGroup:
        return {group_key(map_group.owner()): decode(map_group.concept_maps(), ConceptMap) for map_group in answer}
    elif answer_type is Numeric:
        if answer.is_int():
            return answer.as_int()
        elif answer.is_float():
            return answer.as_float()
        else:
            return math.nan
    elif answer_type is NumericGroup:
        return {group_key(numeric_group.owner()): decode(numeric_group.numeric(), Numeric) for numeric_group in answer}
    else:
        raise ValueError("Unknown answer type. Please report this error.")


def run(connection, query, args, strict_transactions, global_inference):
    query = query.strip()

    if len(query) == 0:
        return

    query_args = "".join(query.split("\"")[::2]).replace(";", "").split()

    keyword_counts = {
        "match": 0,
        "get": 0,
        "define": 0,
        "undefine": 0,
        "insert": 0,
        "delete": 0,
        "group": 0,
        "count": 0,
        "sum": 0,
        "max": 0,
        "min": 0,
        "mean": 0,
        "median": 0,
        "std": 0,
    }

    for arg in query_args:
        if arg in keyword_counts:
            keyword_counts[arg] += 1

    aggregate_count = sum((
        keyword_counts["count"],
        keyword_counts["sum"],
        keyword_counts["max"],
        keyword_counts["min"],
        keyword_counts["mean"],
        keyword_counts["median"],
        keyword_counts["std"],
    ))

    candidate_query_types = list()

    if keyword_counts["group"] > 0 and aggregate_count > 0:
        candidate_query_types.append("match_group_aggregate")
    elif aggregate_count > 0:
        candidate_query_types.append("match_aggregate")
    elif keyword_counts["group"] > 0:
        candidate_query_types.append("match_group")
    elif keyword_counts["get"] > 0:
        candidate_query_types.append("match")

    if keyword_counts["define"] > 0:
        candidate_query_types.append("define")

    if keyword_counts["undefine"] > 0:
        candidate_query_types.append("undefine")

    if keyword_counts["insert"] > 0 and keyword_counts["delete"] > 0:
        candidate_query_types.append("update")
    elif keyword_counts["insert"] > 0:
        candidate_query_types.append("insert")
    elif keyword_counts["delete"] > 0:
        candidate_query_types.append("delete")

    if len(candidate_query_types) > 1:
        raise QueryParsingError("Query contains incompatible keywords: '{}'".format("', '".join(candidate_query_types)))
    elif len(candidate_query_types) == 1:
        query_type = candidate_query_types[0]
    elif keyword_counts["match"] > 0:
        query_type = "match"
    else:
        raise QueryParsingError("Query contains no keywords.")

    if args.session is None:
        if strict_transactions:
            raise ArgumentError("Strict transaction types is enabled and no session type was provided. Use -s to specify session type.")
        elif query_type in ("define", "undefine"):
            session_type = SessionType.SCHEMA
        else:
            session_type = SessionType.DATA
    else:
        if args.session.lower() == "schema":
            session_type = SessionType.SCHEMA
        elif args.session.lower() == "data":
            session_type = SessionType.DATA
        else:
            raise ArgumentError("Incorrect session type provided. Session type must be 'schema' or 'data'.")

    if args.transaction is None:
        if strict_transactions:
            raise ArgumentError("Strict transaction types is enabled and no transaction type was provided. Use -t to specify transaction type.")
        elif query_type in ("define", "undefine", "insert", "update", "delete"):
            transaction_type = TransactionType.WRITE
        else:
            transaction_type = TransactionType.READ
    else:
        if args.transaction.lower() == "read":
            transaction_type = TransactionType.READ
        elif args.transaction.lower() == "write":
            transaction_type = TransactionType.WRITE
        else:
            raise ArgumentError("Incorrect transaction type provided. Transaction type must be 'read' or 'write'.")

    if args.inference is None:
        options = typedb.client.TypeDBOptions().core().set_infer(global_inference)
    else:
        options = typedb.client.TypeDBOptions().core().set_infer(args.inference)

    connection.set_session(session_type)

    try:
        with connection.session.transaction(transaction_type, options) as transaction:
            if query_type == "match":
                results = decode(transaction.query().match(query), ConceptMap)
            elif query_type == "match_aggregate":
                results = decode(transaction.query().match_aggregate(query).get(), Numeric)
            elif query_type == "match_group":
                results = decode(transaction.query().match_group(query), ConceptMapGroup)
            elif query_type == "match_group_aggregate":
                results = decode(transaction.query().match_group_aggregate(query), NumericGroup)
            elif query_type == "define":
                transaction.query().define(query)
            elif query_type == "undefine":
                transaction.query().undefine(query)
            elif query_type == "insert":
                transaction.query().insert(query)
            elif query_type == "delete":
                transaction.query().delete(query)
            elif query_type == "update":
                transaction.query().update(query)

            if transaction_type == TransactionType.WRITE:
                transaction.commit()
                print('{} query success.'.format(query_type.title()))
                return
            else:
                return results
    except TypeDBClientException as exception:
        if session_type == SessionType.SCHEMA:
            print('Switching to data session due to failed schema query.')
            connection.set_session(SessionType.DATA)

        raise exception
