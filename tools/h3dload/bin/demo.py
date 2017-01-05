data = references.getValue()[0]

def initialize():
    print "fntialize"

def traverseSG():
    if data.active.getValue():
        print "active       : ", data.active.getValue()
        print "force        : ", data.force.getValue()
        print "torque       : ", data.torque.getValue()
        print "position     : ", data.position.getValue()
        print "velocity     : ", data.velocity.getValue()
        print "orientation  : ", data.orientation.getValue()
        print "button1      : ", data.button1.getValue()
        print "button2      : ", data.button2.getValue()
        print "button3      : ", data.button3.getValue()
        print "button4      : ", data.button4.getValue()
        print "timestamp    : ", data.timestamp.getValue()
        print "distance     : ", data.distance.getValue()
        print "-----"
