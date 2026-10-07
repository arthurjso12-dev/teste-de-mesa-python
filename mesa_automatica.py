"""Gerador automático de testes de mesa para código Python.

Uso:
  python mesa_automatica.py --file exemplo.py --inputs 1,2,3
  python mesa_automatica.py --code "x = int(input())\ny = x + 5" --inputs 7

O script executa o código em um ambiente controlado e imprime uma tabela de trace
com colunas: linha, código, variáveis, e explicação.
"""

import ast
import argparse
import sys
import textwrap
from typing import Any, Dict, List, Optional, Tuple


class _ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


class MesaTracer(ast.NodeVisitor):
    def __init__(self, source_lines: List[str], input_values: List[str]):
        self.source_lines = source_lines
        self.input_values = input_values
        self.input_index = 0
        self.env: Dict[str, Any] = {}
        self.functions: Dict[str, ast.FunctionDef] = {}
        self.logs: List[Dict[str, Any]] = []
        self.loop_depth = 0

    def log(self, node: ast.AST, action: str, details: str) -> None:
        line = getattr(node, 'lineno', None)
        code = self.source_lines[line - 1].strip() if line is not None else ''
        self.logs.append({
            'line': line,
            'code': code,
            'vars': dict(sorted(self.env.items())),
            'details': details,
        })

    def eval_expr(self, node: ast.expr) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.JoinedStr):
            return ''.join(str(self.eval_expr(value)) for value in node.values)
        if isinstance(node, ast.FormattedValue):
            value = self.eval_expr(node.value)
            if node.conversion == ord('s'):
                value = str(value)
            elif node.conversion == ord('r'):
                value = repr(value)
            elif node.conversion == ord('a'):
                value = ascii(value)
            if node.format_spec is not None:
                return format(value, self.eval_expr(node.format_spec))
            return str(value)
        if isinstance(node, ast.Name):
            name = node.id
            return self.env.get(name, f'<não definido: {name}>')
        if isinstance(node, ast.BinOp):
            left = self.eval_expr(node.left)
            right = self.eval_expr(node.right)
            return self.eval_binop(node.op, left, right)
        if isinstance(node, ast.UnaryOp):
            operand = self.eval_expr(node.operand)
            return self.eval_unaryop(node.op, operand)
        if isinstance(node, ast.BoolOp):
            values = [self.eval_expr(v) for v in node.values]
            return self.eval_boolop(node.op, values)
        if isinstance(node, ast.Compare):
            left = self.eval_expr(node.left)
            comparisons = []
            current = left
            for op, comparator in zip(node.ops, node.comparators):
                right = self.eval_expr(comparator)
                comparisons.append(self.eval_compare(op, current, right))
                current = right
            return all(comparisons)
        if isinstance(node, ast.Call):
            return self.eval_call(node)
        if isinstance(node, ast.List):
            return [self.eval_expr(el) for el in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self.eval_expr(el) for el in node.elts)
        if isinstance(node, ast.Dict):
            return {self.eval_expr(k): self.eval_expr(v) for k,v in zip(node.keys, node.values)}
        if isinstance(node, ast.Subscript):
            value = self.eval_expr(node.value)
            index = self.eval_expr(node.slice) if isinstance(node.slice, ast.expr) else self.eval_expr(node.slice.value)
            return value[index]
        if isinstance(node, ast.Attribute):
            value = self.eval_expr(node.value)
            return getattr(value, node.attr)
        raise NotImplementedError(f'Expressão não suportada: {ast.dump(node)}')

    def eval_binop(self, op: ast.operator, left: Any, right: Any) -> Any:
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            return left / right
        if isinstance(op, ast.FloorDiv):
            return left // right
        if isinstance(op, ast.Mod):
            return left % right
        if isinstance(op, ast.Pow):
            return left ** right
        if isinstance(op, ast.LShift):
            return left << right
        if isinstance(op, ast.RShift):
            return left >> right
        if isinstance(op, ast.BitOr):
            return left | right
        if isinstance(op, ast.BitAnd):
            return left & right
        if isinstance(op, ast.BitXor):
            return left ^ right
        raise NotImplementedError(f'Operador binário não suportado: {op.__class__.__name__}')

    def eval_unaryop(self, op: ast.unaryop, operand: Any) -> Any:
        if isinstance(op, ast.UAdd):
            return +operand
        if isinstance(op, ast.USub):
            return -operand
        if isinstance(op, ast.Not):
            return not operand
        if isinstance(op, ast.Invert):
            return ~operand
        raise NotImplementedError(f'Operador unário não suportado: {op.__class__.__name__}')

    def eval_boolop(self, op: ast.boolop, values: List[Any]) -> Any:
        if isinstance(op, ast.And):
            result = True
            for value in values:
                result = result and value
                if not result:
                    break
            return result
        if isinstance(op, ast.Or):
            result = False
            for value in values:
                result = result or value
                if result:
                    break
            return result
        raise NotImplementedError(f'Boolean operator not supported: {op.__class__.__name__}')

    def eval_compare(self, op: ast.cmpop, left: Any, right: Any) -> bool:
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.NotEq):
            return left != right
        if isinstance(op, ast.Lt):
            return left < right
        if isinstance(op, ast.LtE):
            return left <= right
        if isinstance(op, ast.Gt):
            return left > right
        if isinstance(op, ast.GtE):
            return left >= right
        if isinstance(op, ast.In):
            return left in right
        if isinstance(op, ast.NotIn):
            return left not in right
        if isinstance(op, ast.Is):
            return left is right
        if isinstance(op, ast.IsNot):
            return left is not right
        raise NotImplementedError(f'Comparador não suportado: {op.__class__.__name__}')

    def eval_call(self, node: ast.Call) -> Any:
        func_name = self.get_func_name(node.func)
        if node.keywords:
            raise NotImplementedError('Argumentos nomeados não são suportados em chamadas')
        args = [self.eval_expr(arg) for arg in node.args]
        if func_name == 'input':
            if self.input_index < len(self.input_values):
                value = self.input_values[self.input_index]
                self.input_index += 1
            else:
                value = ''
            self.log(node, 'input()', f'Entrada simulada: "{value}"')
            return value
        if func_name == 'int':
            return int(args[0])
        if func_name == 'float':
            return float(args[0])
        if func_name == 'str':
            return str(args[0])
        if func_name == 'len':
            return len(args[0])
        if func_name == 'range':
            return range(*args)
        if func_name == 'print':
            self.log(node, 'print()', f'Imprime: {args}')
            return None
        if func_name in self.functions:
            result = self.call_function(func_name, args, node)
            self.log(node, 'chamada', f'{func_name} retorna {result!r}')
            return result
        raise NotImplementedError(f'Chamada de função não suportada: {func_name}')

    def call_function(self, func_name: str, args: List[Any], node: ast.Call) -> Any:
        function = self.functions[func_name]
        parameters = function.args.posonlyargs + function.args.args
        if function.args.defaults or function.args.kwonlyargs or function.args.vararg or function.args.kwarg:
            raise NotImplementedError('A função usa parâmetros não suportados')
        if len(args) != len(parameters):
            raise TypeError(f'{func_name} espera {len(parameters)} argumento(s), mas recebeu {len(args)}')

        previous_env = self.env
        self.env = dict(previous_env)
        self.env.update({parameter.arg: value for parameter, value in zip(parameters, args)})
        try:
            for statement in function.body:
                self.visit(statement)
        except _ReturnSignal as result:
            return result.value
        finally:
            self.env = previous_env
        return None

    def get_func_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        raise NotImplementedError(f'Nome de função não suportado: {ast.dump(node)}')

    def visit_Module(self, node: ast.Module) -> None:
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.decorator_list:
            raise NotImplementedError('Decoradores não são suportados em funções')
        self.functions[node.name] = node
        self.log(node, 'def', f'Função {node.name} definida')

    def visit_Assign(self, node: ast.Assign) -> None:
        value = self.eval_expr(node.value)
        targets = [self.format_target(t) for t in node.targets]
        for target in node.targets:
            self.assign_target(target, value)
        self.log(node, 'atribuição', f'{" e ".join(targets)} = {value!r}')

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        target_name = self.format_target(node.target)
        old_value = self.eval_expr(node.target)
        operand = self.eval_expr(node.value)
        new_value = self.eval_binop(node.op, old_value, operand)
        self.assign_target(node.target, new_value)
        self.log(node, 'atribuição aumentada', f'{target_name} de {old_value!r} para {new_value!r}')

    def visit_Expr(self, node: ast.Expr) -> None:
        if isinstance(node.value, ast.Call):
            result = self.eval_call(node.value)
            if result is not None:
                self.log(node, 'expressão', f'Resultado: {result!r}')
        else:
            self.eval_expr(node.value)
            self.log(node, 'expressão', 'Avaliado')

    def visit_If(self, node: ast.If) -> None:
        condition = self.eval_expr(node.test)
        branch = 'Verdadeiro' if condition else 'Falso'
        self.log(node, 'if', f'Condição avaliada como {condition!r} ({branch})')
        if condition:
            for stmt in node.body:
                self.visit(stmt)
        else:
            for stmt in node.orelse:
                self.visit(stmt)

    def visit_While(self, node: ast.While) -> None:
        iteration = 0
        while self.eval_expr(node.test):
            condition = self.eval_expr(node.test)
            self.log(node, 'while', f'Iteração {iteration + 1}: condição {condition!r} é verdadeira')
            for stmt in node.body:
                self.visit(stmt)
            iteration += 1
            if iteration > 1000:
                self.log(node, 'while', 'Loop interrompido após 1000 iterações (segurança)')
                break
        if iteration == 0:
            self.log(node, 'while', 'Condição inicial falsa, corpo não executado')

    def visit_For(self, node: ast.For) -> None:
        iterable = self.eval_expr(node.iter)
        loop_var = self.format_target(node.target)
        if hasattr(iterable, '__iter__'):
            for item in iterable:
                self.assign_target(node.target, item)
                self.log(node, 'for', f'{loop_var} = {item!r} em iteração')
                for stmt in node.body:
                    self.visit(stmt)
        else:
            raise NotImplementedError('Iterável não suportado no for')
        if not list(iterable):
            self.log(node, 'for', 'Iterável vazio, corpo não executado')

    def visit_Return(self, node: ast.Return) -> None:
        value = self.eval_expr(node.value) if node.value else None
        self.log(node, 'return', f'Retorna {value!r}')
        raise _ReturnSignal(value)

    def format_target(self, target: ast.expr) -> str:
        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target, ast.Tuple):
            return ', '.join(self.format_target(elt) for elt in target.elts)
        if isinstance(target, ast.Subscript):
            return f'{self.format_target(target.value)}[{ast.unparse(target.slice)}]'
        raise NotImplementedError(f'Tipo de alvo não suportado: {ast.dump(target)}')

    def assign_target(self, target: ast.expr, value: Any) -> None:
        if isinstance(target, ast.Name):
            self.env[target.id] = value
            return
        if isinstance(target, ast.Subscript):
            target_obj = self.eval_expr(target.value)
            index = self.eval_expr(target.slice) if isinstance(target.slice, ast.expr) else self.eval_expr(target.slice.value)
            target_obj[index] = value
            return
        if isinstance(target, ast.Tuple):
            if not isinstance(value, (tuple, list)) or len(value) != len(target.elts):
                raise ValueError('Desempacotamento inválido')
            for elt, item in zip(target.elts, value):
                self.assign_target(elt, item)
            return
        raise NotImplementedError(f'Atribuição não suportada: {ast.dump(target)}')


def format_table(logs: List[Dict[str, Any]]) -> str:
    headers = ['Linha', 'Código', 'Variáveis', 'Detalhes']
    rows = []
    for log in logs:
        vars_formatted = ', '.join(f'{k}={repr(v)}' for k, v in log['vars'].items())
        rows.append([
            str(log['line'] or ''),
            log['code'],
            vars_formatted,
            log['details'],
        ])
    col_widths = [max(len(row[i]) for row in ([headers] + rows)) for i in range(4)]
    separator = ' | '
    lines = []
    lines.append(separator.join(headers[i].ljust(col_widths[i]) for i in range(4)))
    lines.append(separator.join('-' * col_widths[i] for i in range(4)))
    for row in rows:
        lines.append(separator.join(row[i].ljust(col_widths[i]) for i in range(4)))
    return '\n'.join(lines)


def normalize_code_argument(code: str) -> str:
    return code.replace('\\r\\n', '\r\n').replace('\\n', '\n').replace('\\t', '\t')


def main() -> None:
    parser = argparse.ArgumentParser(description='Gerador de testes de mesa para Python')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--file', '-f', help='Arquivo Python a ser analisado')
    group.add_argument('--code', '-c', help='Código Python em linha única ou multilinha')
    parser.add_argument('--inputs', '-i', help='Valores de input() separados por vírgula', default='')
    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            source = f.read()
    elif args.code:
        source = normalize_code_argument(args.code)
    elif not sys.stdin.isatty():
        source = sys.stdin.read()
    else:
        print('Cole o código Python abaixo. Termine com uma linha vazia e pressione Enter:')
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == '':
                break
            lines.append(line)
        source = '\n'.join(lines)

    if not source or not source.strip():
        parser.error('Nenhum código fornecido. Use --file, --code ou cole o código no prompt.')

    source_lines = source.splitlines()
    input_values = [item.strip() for item in args.inputs.split(',') if item.strip()]

    tree = ast.parse(source)
    tracer = MesaTracer(source_lines, input_values)
    tracer.visit(tree)

    print('\nTeste de mesa automático\n')
    print(format_table(tracer.logs))


if __name__ == '__main__':
    main()
