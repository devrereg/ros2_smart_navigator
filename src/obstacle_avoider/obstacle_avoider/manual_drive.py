# manual_drive.py - 2일차 C: 속도 명령 발행 노드 (TwistStamped)
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import TwistStamped


class ManualDrive(Node):
    def __init__(self):
        super().__init__('manual_drive')
        # mode: stop | forward | rotate | demo
        self.declare_parameter('mode', 'stop')
        self.declare_parameter('linear_x', 0.2)
        self.declare_parameter('angular_z', 0.5)

        self.pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.tick)  # 10Hz

        # demo 시퀀스용 시간 (forward 3s -> stop 1s -> rotate 3s -> stop 유지)
        self.start_time = self.get_clock().now()
        self.get_logger().info(
            f"started mode={self.get_parameter('mode').value} "
            f"(10Hz, TwistStamped)"
        )

    def current_cmd(self):
        mode = self.get_parameter('mode').value
        linear_x = float(self.get_parameter('linear_x').value)
        angular_z = float(self.get_parameter('angular_z').value)

        if mode == 'forward':
            return linear_x, 0.0
        if mode == 'rotate':
            return 0.0, angular_z
        if mode == 'demo':
            elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
            if elapsed < 3.0:
                return linear_x, 0.0      # 직진 3초 (~0.6m)
            if elapsed < 4.0:
                return 0.0, 0.0           # 정지 1초
            if elapsed < 7.0:
                return 0.0, angular_z     # 회전 3초
            return 0.0, 0.0               # 이후 정지 유지
        return 0.0, 0.0  # stop + unknown -> 안전 정지

    def tick(self):
        lin, ang = self.current_cmd()
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.twist.linear.x = lin
        msg.twist.angular.z = ang
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = ManualDrive()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        # 자동 정지 없음: Ctrl+C는 발행만 중단, 로봇은 마지막 명령 유지
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
