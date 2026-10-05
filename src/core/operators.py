from core.types import Op


def arity(op: Op) -> int:
    if op in (Op.AND, Op.OR):
        return 2
    if op == Op.NOT:
        return 1
    raise ValueError(f"Invalid operator: {op}")


def apply_operator(op: Op, inputs: tuple[int, ...]) -> int:
    expected_arity = arity(op)
    if len(inputs) != expected_arity:
        raise ValueError(
            f"{op.name} expects {expected_arity} inputs, got {len(inputs)}"
        )
    if any(value not in (0, 1) for value in inputs):
        raise ValueError(f"Boolean inputs must be 0 or 1, got {inputs}")

    if op == Op.AND:
        return int(all(inputs))
    if op == Op.OR:
        return int(any(inputs))
    if op == Op.NOT:
        return int(not inputs[0])
    raise ValueError(f"Invalid operator: {op}")


def canonicalize_parents(
    op: Op,
    parents: tuple[int, ...],
) -> tuple[int, ...]:
    """Remove operand-order duplicates for commutative operators."""

    if op in (Op.AND, Op.OR):
        return tuple(sorted(parents))
    if op == Op.NOT:
        return parents
    raise ValueError(f"Invalid operator: {op}")
