bringup_can () {
    PORT=$1
    IFACE=$2

    echo $PORT "->" $IFACE

    sudo slcand -o -c -s5 $PORT $IFACE
    sudo ifconfig can0 up
    sudo ifconfig can0 txqueuelen 1000

}

move () {
    POSITION=$1
    DUTY=$2

    CAN_DOWN="ifconfig can0 | grep up"
    if $CAN_DOWN; then
        bringup_can /dev/ttyACM0 can0 
    fi

    python3 python/run.py -p $POSITION -s $DUTY
}