# common.py - manual_drive와 avoider가 공유하는 /cmd_vel 생성 로직
from geometry_msgs.msg import TwistStamped


def make_cmd_vel(node, linear_x, angular_z):
    """header를 채운 TwistStamped를 만든다. (Jazzy + Harmonic은 TwistStamped 필수)"""
    msg = TwistStamped()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.header.frame_id = 'base_link'
    msg.twist.linear.x = linear_x
    msg.twist.angular.z = angular_z
    return msg
