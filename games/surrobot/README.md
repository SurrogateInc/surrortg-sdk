# Surrobot

## How to run for development

The surrobot game template can be run with:
`pipenv run surrobot`

The surrobot implementation has mock classes for hardware so the code can be
run on other devices than the physical bot. To enable the mocks use:
`MOCK_HW=True pipenv run surrobot`

## GPIO Layout

- GPIO 0 - Not connected
- GPIO 1 - Not connected
- GPIO 2 - I2C SDA
- GPIO 3 - I2C SCL
- GPIO 4 - I2C sensor GPIO
- GPIO 5 - Servo 7
- GPIO 6 - Motor RL 1
- GPIO 7 - SPI CE1
- GPIO 8 - SPI CE0
- GPIO 9 - SPI0 MISO
- GPIO 10 - SPI0 MOSI
- GPIO 11 - SPI0 SCLK
- GPIO 12 - Motor RL 2
- GPIO 13 - Motor RR 2
- GPIO 14 - UART TX
- GPIO 15 - UART RX
- GPIO 16 - Motor FL 1
- GPIO 17 - Servo 1
- GPIO 18 - Servo 8 (also LED matrix HW pwm pin)
- GPIO 19 - Motor RR 1
- GPIO 20 - Motor FL 2
- GPIO 21 - Motor FR 2
- GPIO 22 - Servo 3
- GPIO 23 - Servo 6
- GPIO 24 - Servo 5
- GPIO 25 - Servo 4
- GPIO 26 - Motor FR 1
- GPIO 27 - Servo 2
