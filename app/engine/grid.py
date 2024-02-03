
from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple, Iterator
from app.objects import GameObject, Asset
from app.objects.ninjas import Ninja
from app.data.constants import Phase

if TYPE_CHECKING:
    from app.engine.penguin import Penguin
    from app.engine.game import Game

import random

class Grid:
    def __init__(self, game: "Game") -> None:
        self.array: List[List[GameObject | None]] = [[None] * 5 for _ in range(9)]
        self.tiles: List[GameObject] = []
        self.enemy_spawns = [range(6, 9), range(5)]
        self.game = game

    def __repr__(self) -> str:
        return f"<Grid ({self.array})>"

    def __getitem__(self, index: Tuple[int, int]) -> GameObject | None:
        if self.is_valid(*index):
            return self.array[index[0]][index[1]]

    def __setitem__(self, index: Tuple[int, int], value: GameObject | None) -> None:
        self.array[index[0]][index[1]] = value

        if value is not None:
            value.x, value.y = index[0], index[1]

    def add(self, obj: GameObject) -> None:
        """Add a game object to the grid"""
        self.__setitem__((obj.x, obj.y), obj)

    def remove(self, obj: GameObject) -> None:
        """Remove a game object from the grid"""
        x, y = self.coordinates(obj)
        self[x, y] = None

    def move(self, obj: GameObject, x: int, y: int) -> None:
        """Move a game object to a new location"""
        self.remove(obj)
        self[x, y] = obj

    def coordinates(self, obj: GameObject) -> Tuple[int, int]:
        """Get the coordinates of an object"""
        for x in range(9):
            for y in range(5):
                if self[x, y] != obj:
                    continue
                return (x, y)
        return (-1, -1)

    def enemy_spawn_location(self, max_attempts=100) -> Tuple[int, int]:
        """Get a random enemy spawn location"""
        for _ in range(max_attempts):
            x = random.choice(self.enemy_spawns[0])
            y = random.choice(self.enemy_spawns[1])

            if self.can_move(x, y):
                return (x, y)

        return (-1, -1)

    def is_valid(self, x: int, y: int) -> bool:
        """Check if a tile is valid"""
        return x in range(9) and y in range(5)

    def can_move(self, x: int, y: int) -> bool:
        """Check if a tile is empty"""
        if x not in range(9) or y not in range(5):
            return False

        return self[x, y] is None

    def can_move_to_tile(self, ninja: Ninja, x: int, y: int) -> bool:
        """Check if a ninja can move to a tile"""
        if x not in range(9) or y not in range(5):
            return False

        if not self.can_move(x, y):
            return False

        distance = abs(x - ninja.x) + abs(y - ninja.y)

        return distance <= ninja.move

    def initialize_tiles(self) -> None:
        """Initialize the tiles, and the tile frame"""
        tile_frame = GameObject(self.game, 'ui_tile_frame')
        tile_frame.assets.add(Asset.from_name('ui_tile_frame'))
        tile_frame.assets.add(Asset.from_name('blank_png'))
        tile_frame.place_object()

        for x in range(9):
            for y in range(5):
                tile = GameObject(
                    self.game,
                    f'{x}-{y}',
                    x,
                    y,
                    on_click=self.on_tile_click,
                    x_offset=0.5,
                    y_offset=0.9998
                )
                tile.assets.add(Asset.from_name('ui_tile_move'))
                tile.assets.add(Asset.from_name('ui_tile_attack'))
                tile.assets.add(Asset.from_name('ui_tile_heal'))
                tile.assets.add(Asset.from_name('ui_tile_no_move'))
                tile.assets.add(Asset.from_name('blank_png'))
                self.tiles.append(tile)
                tile.place_object()

    def show_tiles(self) -> None:
        tile_frame = self.game.objects.by_name('ui_tile_frame')
        tile_frame.place_sprite('ui_tile_frame')

        for client in self.game.clients:
            for tile in client.ninja.movable_tiles():
                tile.place_sprite('ui_tile_move', client)

    def hide_tiles(self) -> None:
        tile_frame = self.game.objects.by_name('ui_tile_frame')
        tile_frame.hide()

        for tile in self.tiles:
            tile.hide()

    def change_tile_sprites(self, name: str) -> None:
        for client in self.game.clients:
            for tile in client.ninja.movable_tiles():
                tile.place_sprite(name, client)

    def get_tile(self, x: int, y: int) -> GameObject | None:
        """Get a tile by its coordinates"""
        return next((tile for tile in self.tiles if tile.x == x and tile.y == y), None)

    def on_tile_click(self, client: "Penguin", tile: GameObject, *args) -> None:
        ninja = self.game.objects.by_name(client.element.capitalize())
        ninja.place_ghost(tile.x, tile.y)

        if client.tip_mode and client.last_tip == Phase.MOVE:
            client.game.hide_tip(client)

    def surrounding_tiles(self, center_x: int, center_y: int, distance: int = 1) -> Iterator[GameObject]:
        x_range = range(center_x - distance, center_x + distance + 1)
        y_range = range(center_y - distance, center_y + distance + 1)

        for x in x_range:
            for y in y_range:
                if not self.is_valid(x, y):
                    continue

                if x == center_x and y == center_y:
                    continue

                yield self.get_tile(x, y)

    def surrounding_objects(self, x: int, y: int, distance: int = 1) -> Iterator[GameObject]:
        tiles = self.surrounding_tiles(x, y, distance)

        for tile in tiles:
            if (object := self[tile.x, tile.y]) is not None:
                yield object
