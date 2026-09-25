"""Userspace Kernel Intelligence — NOT an operating-system kernel.

See ``context.KernelIntelligence`` for the public facade.
"""

from aetheros.kernel.context import KernelIntelligence, ResourceContext

__all__ = [
    "KernelIntelligence",
    "ResourceContext",
]
