#
# Copyright (C) 2023 Vaticle
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
class Label:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

class Var:
    _INTERNAL = 0
    def __init__(self, name):
        self.name = name

    @classmethod
    def next_internal(cls):
        cls._INTERNAL += 1
        return "$INTERNAL__{}".format(cls._INTERNAL)

    def __str__(self):
        return self.name

class Literal:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

class Comparator:
    def __init__(self, symbol):
        self.symbol = symbol

    def __str__(self):
        return self.symbol

# Constraints

class Constraint:
    def may_set_lhs(self, lhs: Var):
        pass

class BinaryConstraint(Constraint):
    def __init__(self, lhs:Var, rhs:Var):
        self.lhs = lhs
        self.rhs = rhs

    def may_set_lhs(self, lhs: Var):
        assert self.lhs is None
        self.lhs = lhs

    def __str__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.lhs, self.rhs)

class Isa(BinaryConstraint):
    def __init__(self, lhs: Var, rhs: Var):
        super().__init__(lhs, rhs)

class Has(BinaryConstraint):
    def __init__(self, lhs: Var, rhs: Var):
        super().__init__(lhs, rhs)

class Links(BinaryConstraint):
    def __init__(self, lhs: Var, rhs: Var, role): # role would ideally be Var, but we don't have a rolename keyword
        super().__init__(lhs, rhs)
        self.role = role


# TODO: Deprecate
class IsaType(Constraint):
    def __init__(self, lhs: Var, rhs: Label):
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.lhs, self.rhs)

    def may_set_lhs(self, lhs: Var):
        if self.lhs is None:
            self.lhs = lhs

class AttributeLabelValue(Constraint):
    def __init__(self, lhs: Var, label: Label, value: Literal):
        self.lhs = lhs
        self.label = label
        self.value = value

    def __str__(self):
        return "{}({}, {}, {})".format(self.__class__.__name__, self.lhs, self.label, self.value)

class Comparison(Constraint):
    def __init__(self, lhs: Var, rhs: Label, comparator):
        self.lhs = lhs
        self.rhs = rhs
        self.comparator = comparator

    def __str__(self):
        return "{}({}, {}, {})".format(self.__class__.__name__, self.lhs, self.comparator, self.rhs)


class Assign(Constraint): # Not sub edge
    # Treat RHS as black box.
    def __init__(self, lhs: Var, rhs):
        self.assigned = lhs
        self.expr = rhs

    def __str__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.lhs, self.rhs)

# TODO: Add schema edges
