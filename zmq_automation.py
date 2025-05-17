import zmq
import subprocess

def bring_up_docker():
    try:
        # Run docker-compose up -d and capture output
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print("Docker Compose Up succeeded:\n", result.stdout.decode())
        return True
    except subprocess.CalledProcessError as e:
        print("Docker Compose Up failed:\n", e.stderr.decode())
        return False

def main():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    print("ZMQ replier listening on port 5555...")

    while True:
        #  Wait for next request from client
        message = socket.recv_string()
        print(f"Received: {message}")

        if message == "start_voice_command":
            success = bring_up_docker()
            if success:
                socket.send_string("start_voice_command_ack")
            else:
                socket.send_string("docker_up_failed")
        else:
            socket.send_string("unknown_command")

if name == "__main__":
    main()