"""Pymunk 2D physics simulation for Fruit Merge."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
import pymunk
from fruit_merge.constants import (
    COLLISION_TYPE_FRUIT,
    COLLISION_TYPE_WALL,
    CONTAINER_BOTTOM,
    CONTAINER_LEFT,
    CONTAINER_RIGHT,
    CONTAINER_TOP,
    DEFAULT_ELASTICITY,
    DEFAULT_FRICTION,
    DROP_Y,
    FRUIT_TIERS,
    GRAVITY,
    MAX_TIER,
    PHYSICS_SUBSTEPS,
    WALL_FLOOR_ELASTICITY,
    WALL_FRICTION,
    WALL_SIDE_ELASTICITY,
    WALL_THICKNESS,
    FruitConfig,
)


@dataclass
class MergeEvent:
    tier: int               # The tier that merged (e.g., two tier 1s merged)
    new_tier: Optional[int] # The resulting tier (None if max tier cleared)
    x: float
    y: float
    score: int
    new_fruit_id: Optional[int]


class PhysicsManager:
    """Controls the 2D rigid-body physics world, container walls, and fruit collisions."""

    def __init__(self, gravity: float = GRAVITY):
        self.space = pymunk.Space()
        self.space.gravity = (0, gravity)
        self.space.damping = 0.92  # Air resistance for stable stacking

        self.fruits: Dict[int, Tuple[pymunk.Body, pymunk.Circle, int]] = {}  # id -> (body, shape, tier)
        self._next_id = 1
        self._merging_ids: Set[int] = set()
        self._pending_merges: List[Tuple[int, int, int]] = []  # (id_a, id_b, tier)

        self._init_walls()
        self._init_collision_handler()

    def _init_walls(self) -> None:
        """Constructs static container boundaries with smooth full-height drop channels and chamfered floor."""
        static_body = self.space.static_body

        corner_inset = 18.0
        # Bottom floor: soft landing prevents high trampoline rebounds
        floor = pymunk.Segment(
            static_body,
            (CONTAINER_LEFT + corner_inset, CONTAINER_BOTTOM),
            (CONTAINER_RIGHT - corner_inset, CONTAINER_BOTTOM),
            WALL_THICKNESS / 2.0,
        )
        floor.elasticity = WALL_FLOOR_ELASTICITY
        floor.friction = WALL_FRICTION
        floor.collision_type = COLLISION_TYPE_WALL

        # Smooth vertical drop guide chute: side walls extend upward past DROP_Y (y = 25.0)
        # down to the floor chamfer, guaranteeing that falling fruits glide into the jar mouth
        # smoothly without any corner collisions or ricocheting off the jar opening.
        DROP_CHUTE_TOP = 25.0

        # Left wall: extends from drop chute top down to floor
        left_wall = pymunk.Segment(
            static_body,
            (CONTAINER_LEFT, DROP_CHUTE_TOP),
            (CONTAINER_LEFT, CONTAINER_BOTTOM - corner_inset),
            WALL_THICKNESS / 2.0,
        )
        left_wall.elasticity = WALL_SIDE_ELASTICITY  # 0.0: zero bounce absorbs lateral energy
        left_wall.friction = WALL_FRICTION
        left_wall.collision_type = COLLISION_TYPE_WALL

        # Right wall: extends from drop chute top down to floor
        right_wall = pymunk.Segment(
            static_body,
            (CONTAINER_RIGHT, DROP_CHUTE_TOP),
            (CONTAINER_RIGHT, CONTAINER_BOTTOM - corner_inset),
            WALL_THICKNESS / 2.0,
        )
        right_wall.elasticity = WALL_SIDE_ELASTICITY  # 0.0: zero bounce absorbs lateral energy
        right_wall.friction = WALL_FRICTION
        right_wall.collision_type = COLLISION_TYPE_WALL

        # Bottom-left corner chamfer
        corner_bl = pymunk.Segment(
            static_body,
            (CONTAINER_LEFT, CONTAINER_BOTTOM - corner_inset),
            (CONTAINER_LEFT + corner_inset, CONTAINER_BOTTOM),
            WALL_THICKNESS / 2.0,
        )
        corner_bl.elasticity = WALL_FLOOR_ELASTICITY
        corner_bl.friction = WALL_FRICTION
        corner_bl.collision_type = COLLISION_TYPE_WALL

        # Bottom-right corner chamfer
        corner_br = pymunk.Segment(
            static_body,
            (CONTAINER_RIGHT - corner_inset, CONTAINER_BOTTOM),
            (CONTAINER_RIGHT, CONTAINER_BOTTOM - corner_inset),
            WALL_THICKNESS / 2.0,
        )
        corner_br.elasticity = WALL_FLOOR_ELASTICITY
        corner_br.friction = WALL_FRICTION
        corner_br.collision_type = COLLISION_TYPE_WALL

        self.space.add(floor, left_wall, right_wall, corner_bl, corner_br)

    def _init_collision_handler(self) -> None:
        """Sets up the collision detection for fruit-to-fruit contact."""
        self.space.on_collision(
            COLLISION_TYPE_FRUIT,
            COLLISION_TYPE_FRUIT,
            begin=self._handle_fruit_collision,
        )

    def _handle_fruit_collision(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> bool:
        shape_a, shape_b = arbiter.shapes
        id_a = getattr(shape_a, "fruit_id", None)
        id_b = getattr(shape_b, "fruit_id", None)
        tier_a = getattr(shape_a, "tier", None)
        tier_b = getattr(shape_b, "tier", None)

        if id_a is None or id_b is None or tier_a is None or tier_b is None:
            return True

        if id_a == id_b:
            return True

        # Check if identical tier and neither fruit is already marked for merge
        if tier_a == tier_b:
            if id_a not in self._merging_ids and id_b not in self._merging_ids:
                self._merging_ids.add(id_a)
                self._merging_ids.add(id_b)
                self._pending_merges.append((id_a, id_b, tier_a))

        return True

    def spawn_fruit(self, tier: int, x: float, y: float, vx: float = 0.0, vy: float = 0.0) -> int:
        """Spawns a new dynamic fruit body and circular shape in the physics world."""
        cfg = FRUIT_TIERS[tier]
        mass = cfg.mass
        radius = cfg.radius
        moment = pymunk.moment_for_circle(mass, 0, radius)

        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        body.velocity = (vx, vy)

        shape = pymunk.Circle(body, radius)
        shape.elasticity = DEFAULT_ELASTICITY
        shape.friction = DEFAULT_FRICTION
        shape.collision_type = COLLISION_TYPE_FRUIT

        fruit_id = self._next_id
        self._next_id += 1

        shape.fruit_id = fruit_id
        shape.tier = tier
        body.fruit_id = fruit_id

        self.space.add(body, shape)
        self.fruits[fruit_id] = (body, shape, tier)
        return fruit_id

    def remove_fruit(self, fruit_id: int) -> bool:
        """Safely removes a fruit body and its shape from the simulation."""
        if fruit_id in self.fruits:
            body, shape, _ = self.fruits.pop(fruit_id)
            self.space.remove(shape, body)
            self._merging_ids.discard(fruit_id)
            return True
        return False

    def step(self, dt: float) -> List[MergeEvent]:
        """Advances the simulation by dt in sub-steps and resolves all pending merges."""
        sub_dt = dt / PHYSICS_SUBSTEPS
        for _ in range(PHYSICS_SUBSTEPS):
            self.space.step(sub_dt)

        merge_events: List[MergeEvent] = []

        if self._pending_merges:
            merges_to_process = list(self._pending_merges)
            self._pending_merges.clear()

            for id_a, id_b, tier in merges_to_process:
                if id_a not in self.fruits or id_b not in self.fruits:
                    continue

                body_a, shape_a, _ = self.fruits[id_a]
                body_b, shape_b, _ = self.fruits[id_b]

                pos_a = body_a.position
                pos_b = body_b.position
                mid_x = (pos_a.x + pos_b.x) / 2.0
                mid_y = (pos_a.y + pos_b.y) / 2.0

                vel_a = body_a.velocity
                vel_b = body_b.velocity
                comb_vx = (vel_a.x + vel_b.x) * 0.35
                comb_vy = (vel_a.y + vel_b.y) * 0.35

                # Remove the two merging fruits
                self.remove_fruit(id_a)
                self.remove_fruit(id_b)

                # Determine new tier and score
                current_cfg = FRUIT_TIERS[tier]
                if tier < MAX_TIER:
                    new_tier = tier + 1
                    new_cfg = FRUIT_TIERS[new_tier]
                    score = new_cfg.score

                    # Clamp spawn position to inside boundaries
                    clamped_x = max(
                        CONTAINER_LEFT + new_cfg.radius + 2,
                        min(CONTAINER_RIGHT - new_cfg.radius - 2, mid_x),
                    )
                    clamped_y = min(CONTAINER_BOTTOM - new_cfg.radius - 2, mid_y)

                    new_id = self.spawn_fruit(new_tier, clamped_x, clamped_y, comb_vx, comb_vy)
                    merge_events.append(
                        MergeEvent(
                            tier=tier,
                            new_tier=new_tier,
                            x=clamped_x,
                            y=clamped_y,
                            score=score,
                            new_fruit_id=new_id,
                        )
                    )
                else:
                    # Maximum tier merge (Two Watermelons): Bonus 5000 points and explosion!
                    score = 5000
                    merge_events.append(
                        MergeEvent(
                            tier=tier,
                            new_tier=None,
                            x=mid_x,
                            y=mid_y,
                            score=score,
                            new_fruit_id=None,
                        )
                    )

        return merge_events

    def get_fruit_state(self, fruit_id: int) -> Optional[Tuple[float, float, float, int]]:
        """Returns (x, y, angle_radians, tier) for the specified fruit."""
        if fruit_id in self.fruits:
            body, _, tier = self.fruits[fruit_id]
            return body.position.x, body.position.y, body.angle, tier
        return None

    def get_all_fruits_state(self) -> List[Tuple[int, float, float, float, int]]:
        """Returns list of (fruit_id, x, y, angle, tier) for all active fruits."""
        result = []
        for fid, (body, _, tier) in self.fruits.items():
            result.append((fid, body.position.x, body.position.y, body.angle, tier))
        return result

    def check_overflow(self, danger_y: float) -> Tuple[bool, float]:
        """
        Checks if any fruit has settled above the danger line.
        Returns (is_overflowing, highest_y).
        A fruit is considered settled/overflowing if its top edge (y - radius) is above danger_y
        AND its vertical velocity is low (settled, not just briefly bouncing/dropping).
        """
        highest_y = float("inf")
        overflowing = False

        for fid, (body, shape, tier) in self.fruits.items():
            r = shape.radius
            top_y = body.position.y - r
            vy = abs(body.velocity.y)

            # Settled or slowly moving fruit with top above danger line
            if top_y < danger_y and vy < 35.0:
                overflowing = True
                if top_y < highest_y:
                    highest_y = top_y

        return overflowing, highest_y

    def reset(self) -> None:
        """Clears all fruits from the physics simulation."""
        for fid in list(self.fruits.keys()):
            self.remove_fruit(fid)
        self._pending_merges.clear()
        self._merging_ids.clear()
