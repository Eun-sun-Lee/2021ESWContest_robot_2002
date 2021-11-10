from Brain.Robot import Robot
from enum import Enum, auto
from Brain.InDoorMission import InDoorMission
from Brain.OutDoorMission import OutDoorMission
from Brain.RoomMission import RoomMission, GreenRoomMission, BlackRoomMission
from Constant import Direction, AreaColor, LineColor, WalkInfo

import time

CLEAR_LIMIT: int = 3
class Mode(Enum):
    START = auto()
    IN = auto()
    DETECT_DIRECTION = auto()
    CHECK_AREA_COLOR = auto()
    ROOM_MISSION = auto()
    GO_TO_NEXT_ROOM = auto()
    OUT = auto()
    END = auto()

class Controller:
    robot: Robot = Robot()
    mode: Mode = Mode.START
    mission_done: int = 0
    InDoorMission.set_robot(robot)
    OutDoorMission.set_robot(robot)
    RoomMission.set_robot(robot)
    robot.set_basic_form()
    ROI = False
    @classmethod
    def set_test_mode(cls, mode: Mode) -> None:
        cls.mode = mode
        if cls.mode == Mode.CHECK_AREA_COLOR:
            cls.ROI = False
            cls.robot.color=LineColor.GREEN
            cls.robot.direction = Direction.LEFT
        elif cls.mode == Mode.GO_TO_NEXT_ROOM:
            cls.ROI = True
            cls.robot.color=LineColor.YELLOW
            cls.robot.direction = Direction.LEFT
        elif cls.mode == Mode.OUT:
            cls.ROI = True
            cls.robot.color=LineColor.YELLOW
            cls.robot.direction = Direction.LEFT
            cls.mission_done = 3
            

    @classmethod
    def check_go_to_next_room(cls) -> bool:
        return False if cls.mission_done > CLEAR_LIMIT else True

    @classmethod
    def go_to_next_room(cls) -> bool :
        
        
        if cls.robot.walk_info == WalkInfo.STRAIGHT:
            cls.robot._motion.walk('FORWARD', 2)
        elif cls.robot.walk_info == WalkInfo.V_LEFT:
            cls.robot._motion.walk('LEFT', 1)
        elif cls.robot.walk_info == WalkInfo.V_RIGHT:
            cls.robot._motion.walk('RIGHT', 1)
        elif cls.robot.walk_info == WalkInfo.MODIFY_LEFT:
            cls.robot._motion.turn('LEFT', 1)
        elif cls.robot.walk_info == WalkInfo.MODIFY_RIGHT:
            cls.robot._motion.turn('RIGHT', 1)
        
        elif cls.robot.walk_info == WalkInfo.CORNER_LEFT:
            cls.robot._motion.walk('FORWARD', 1)
            if cls.robot.direction == Direction.RIGHT and cls.robot.line_info['H_Y'] < 100:
                return True
            else:
                if cls.mission_done >= CLEAR_LIMIT:
                    return True
                
        elif cls.robot.walk_info == WalkInfo.CORNER_RIGHT:
            cls.robot._motion.walk('FORWARD', 1)
            if cls.robot.direction == Direction.LEFT and cls.robot.line_info['H_Y' < 100]:
                return True
            else:
                if cls.mission_done >= CLEAR_LIMIT:
                    return True
                
        else: # WalkInfo.BACKWARD, WalkInfo.DIRECTION_LINE
            cls.robot._motion.walk('BACKWARD', 1)
        return False

    @classmethod
    def detect_direction(cls) -> bool:
        direction = cls.robot._image_processor.get_arrow_direction()
        
        if direction:
            cls.robot.direction = Direction.LEFT if direction == "LEFT" else Direction.RIGHT
            cls.robot._motion.set_head(dir='DOWN', angle=10)
            time.sleep(0.5)
        
            cls.robot._motion.walk('FORWARD', 2)
            cls.robot._motion.walk(cls.robot.direction.name, wide=True, loop = 4)
            cls.robot._motion.turn(cls.robot.direction.name, sliding=True, loop = 4)
            return True
        
        cls.robot._motion.walk("BACKWARD", 1)
        time.sleep(1.0)
        return False
    @classmethod
    def room_run(cls):
        cls.robot.color = LineColor.YELLOW
        cls.robot.set_line_and_edge_info(ROI=cls.ROI)
        Mission = GreenRoomMission
        return Mission.run()
        

    @classmethod
    def run(cls):
        mode = cls.mode
        cls.robot.set_line_and_edge_info(ROI=cls.ROI)
        print(mode.name)
        if mode == Mode.START:
            cls.mode = Mode.IN
            cls.ROI = True

        elif mode == Mode.IN:
            if InDoorMission.run():
                cls.mode = Mode.DETECT_DIRECTION
                cls.ROI = False

        elif mode == Mode.DETECT_DIRECTION:
            if cls.detect_direction():
                cls.mode = Mode.GO_TO_NEXT_ROOM
                cls.ROI = True
        
        elif mode == Mode.GO_TO_NEXT_ROOM:
            if cls.go_to_next_room():
                if cls.mission_done < CLEAR_LIMIT:
                    cls.mode = Mode.CHECK_AREA_COLOR  # 미션
                    cls.ROI = False
                    cls.robot.color = LineColor.GREEN
                else:
                    if OutDoorMission.run():
                        return True # 퇴장

        elif mode == Mode.CHECK_AREA_COLOR:
            if RoomMission.check_area_color():
                cls.mode = Mode.ROOM_MISSION

        elif mode == Mode.ROOM_MISSION:
            Mission = GreenRoomMission if RoomMission.area_color == AreaColor.GREEN else BlackRoomMission
            if Mission.run():
                cls.mission_done += 1
                cls.ROI = True
                if cls.check_go_to_next_room():
                    cls.mode = Mode.GO_TO_NEXT_ROOM
                else:
                    cls.mode = Mode.OUT
                    
        return False
