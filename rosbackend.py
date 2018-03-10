from backendbase import BackendBase, call_callbacks_in

import rospy
from std_msgs.msg import String, UInt32
from sensor_msgs.msg import Image

from PIL import Image as pil_image
import base64
from StringIO import StringIO
import numpy as np

try:
    from vizbox.msg import Story
except ImportError as e:
    rospy.logerr(e)


class RosBackend(BackendBase):
    __instance = None


    @staticmethod
    def get_instance(*args, **kwargs):
        if not RosBackend.__instance:
            RosBackend.__instance = RosBackend(*args, **kwargs)
        return RosBackend.__instance

    def __init__(self, shutdown_hook):

        super(RosBackend, self).__init__()
        rospy.init_node("vizbox", log_level=rospy.INFO)
        print "Node initialized"

        rospy.on_shutdown(shutdown_hook)

        self.__encoding = {'bgr8':self.rgba2base64}

        self.op_sub = rospy.Subscriber("sara_command", String, call_callbacks_in(self.on_operator_text, lambda rosmsg: rosmsg.data), queue_size=100)
        self.robot_sub = rospy.Subscriber("sara_said", String, call_callbacks_in(self.on_robot_text, lambda rosmsg: rosmsg.data), queue_size=100)
        self.step_sub = rospy.Subscriber("challenge_step", UInt32, call_callbacks_in(self.on_challenge_step, lambda rosmsg: rosmsg.data), queue_size=100)
        self.image_sub = rospy.Subscriber("/darknet_ros/detection_image", Image, call_callbacks_in(self.on_image, self.ros_image_to_base64), queue_size=1)
        
        try:
            self.story_sub = rospy.Subscriber("story", Story, call_callbacks_in(self.on_story, lambda rosmsg: (rosmsg.title, rosmsg.storyline)), queue_size=100)
        except NameError, e:
            rospy.logerr("To dynamically define a Story, catkin_make this package")

        self.cmd_pub = rospy.Publisher("command", String, queue_size=1)

    def accept_command(self, command_text):
        self.cmd_pub.publish(command_text)

    def ros_image_to_base64(self, rosmsg):
        import random
        # return random.choice([DUMMY1, DUMMY2])
        print rosmsg.encoding, rosmsg.width, rosmsg.height, len(rosmsg.data)

        return self.__encoding[rosmsg.encoding](rosmsg)

    @staticmethod
    def rgba2base64(rosmsg):
        length = len(rosmsg.data)
        bytes_needed = int(rosmsg.width * rosmsg.height * 3)
        # print "encode: length={} width={}, heigth={}, bytes_needed={}".format(length, width, height, bytes_needed)

        converted = pil_image.frombytes('RGB',
                                        (rosmsg.width, rosmsg.height),
                                        rosmsg.data)
        data = np.array(converted)
        red, green, blue = data.T
        data = np.array([blue, green, red])
        data = data.transpose()
        converted = pil_image.fromarray(data)


        string_buffer = StringIO()
        converted.save(string_buffer, "png")
        image_bytes = string_buffer.getvalue()
        encoded = base64.standard_b64encode(image_bytes)
        return encoded