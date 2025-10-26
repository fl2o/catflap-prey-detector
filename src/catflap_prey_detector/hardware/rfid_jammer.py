from gpiozero import OutputDevice

# GPIO 26 = BCM numbering
relay = OutputDevice(26, active_high=True, initial_value=False)

def block_catflap():
    relay.on()

def unblock_catflap():
    relay.off()


if __name__ == "__main__":
    input("Press Enter to block the catflap")
    block_catflap()
    input("Press Enter to unblock the catflap")
    unblock_catflap()