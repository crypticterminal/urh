import numpy as np

from urh.dev.VirtualDevice import Mode, VirtualDevice
from urh.util.RingBuffer import RingBuffer


class EndlessSender(object):
    """
    Enter endless send mode for a device and send data if data gets pushed to ringbuffer.
    """
    BUFFER_SIZE_MB = 100

    def __init__(self, backend_handler, name: str):
        self.__device = VirtualDevice(backend_handler=backend_handler, name=name, mode=Mode.send)
        self.ringbuffer = RingBuffer(int(self.BUFFER_SIZE_MB * 10 ** 6) // 8)
        self.__device.continuous_send_ring_buffer = self.ringbuffer
        self.__device.is_send_continuous = True
        self.__device.num_sending_repeats = 0

    @property
    def device(self) -> VirtualDevice:
        return self.__device

    @device.setter
    def device(self, value: VirtualDevice):
        self.__device = value
        self.__device.is_send_continuous = True
        self.__device.num_sending_repeats = 0
        self.__device.continuous_send_ring_buffer = self.ringbuffer

    @property
    def device_name(self) -> str:
        return self.device.name

    @device_name.setter
    def device_name(self, value: str):
        if value != self.device_name:
            self.device = VirtualDevice(backend_handler=self.device.backend_handler, name=value, mode=Mode.send)

    def start(self):
        self.device.start()

    def stop(self):
        self.device.stop("EndlessSender stopped.")

    def push_data(self, data: np.ndarray):
        self.ringbuffer.push(data)


if __name__ == '__main__':
    from urh.dev.BackendHandler import BackendHandler
    from urh.signalprocessing.Message import Message
    from urh.signalprocessing.MessageType import MessageType
    from urh.signalprocessing.Modulator import Modulator
    from urh.util.Logger import logger
    import time

    endless_sender = EndlessSender(BackendHandler(), "HackRF")
    msg = Message([1, 0] * 16 + [1, 1, 0, 0] * 8 + [0, 0, 1, 1] * 8 + [1, 0, 1, 1, 1, 0, 0, 1, 1, 1] * 4, 0,
                  MessageType("empty_message_type"))
    modulator = Modulator("test_modulator")
    modulator.samples_per_bit = 1000
    modulator.carrier_freq_hz = 55e3
    modulator.modulate(msg.encoded_bits)

    modulator.modulated_samples.tofile("/tmp/test.complex")

    logger.debug("Starting endless sender")
    endless_sender.start()
    time.sleep(1)
    logger.debug("Pushing data")
    endless_sender.push_data(modulator.modulated_samples)
    logger.debug("Pushed data")
    time.sleep(5)
    logger.debug("Stopping endless sender")
    endless_sender.stop()
    time.sleep(1)
    logger.debug("bye")
