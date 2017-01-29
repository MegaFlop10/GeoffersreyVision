# GeoffersreyVision
Vision testing etc.

Vision code for the 2017 FRC game. This is used by 5985 to hopefully track the gear lift and high goal.

To use, run 'vision.py' on a Raspberry Pi or other device on the robot network.

When the 'request' key is True on the networktable, vision.py will process an image and update data onto the network table.
This system isn't designed for a lot of requests per second, use it to find your location and use the other robot sensors.
