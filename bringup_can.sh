bringup_can () {
    PORT=$1
    IFACE=$2

    echo $PORT "->" $IFACE

    sudo slcand -o -c -s5 $PORT $IFACE
    sudo ifconfig can0 up
    sudo ifconfig can0 txqueuelen 1000

}