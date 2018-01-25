/*
Tiny85Ducky is a fork of TrinketKeyboard (https://github.com/adafruit/Adafruit-Trinket-USB) by Adafruit, copyright 2013.

Copyright (c) 2018 FalseAscension
All rights reserved.

Tiny85Ducky is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

Tiny85Ducky is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with Tiny85Ducky. If not, see
<http://www.gnu.org/licenses/>.
*/

#include "usbconfig.h"
#include "usbdrv/usbdrv.h"
#include "keys.h"

#include <avr/power.h>
#include <util/delay.h>

#define F_CPU 16500000UL

uint8_t report_buffer[8];
char usb_hasCommed = 0;
uint8_t idle_rate = 500 / 4;  // see HID1_11.pdf sect 7.2.4
uint8_t protocol_version = 0; // see HID1_11.pdf sect 7.2.6
uint8_t led_state = 0; // caps/num/scroll lock LEDs

void usbBegin()
{
	cli();

	// fake a disconnect to force the computer to re-enumerate
	PORTB &= ~(_BV(USB_CFG_DMINUS_BIT) | _BV(USB_CFG_DPLUS_BIT));
	usbDeviceDisconnect();
	_delay_ms(250);
	usbDeviceConnect();

	// start the USB driver
	usbInit();
	sei();
}

void usbReportSend()
{
	// perform usb background tasks until the report can be sent, then send it
	while (1)
	{
		usbPoll(); // this needs to be called at least once every 10 ms
		if (usbInterruptIsReady())
		{
			usbSetInterrupt((uint8_t*)report_buffer, 8); // send
			break;

			// see http://vusb.wikidot.com/driver-api
		}
	}
}

// USB HID report descriptor for boot protocol keyboard
// see HID1_11.pdf appendix B section 1
// USB_CFG_HID_REPORT_DESCRIPTOR_LENGTH is defined in usbconfig (it's supposed to be 63)
const PROGMEM char usbHidReportDescriptor[USB_CFG_HID_REPORT_DESCRIPTOR_LENGTH] = {
	0x05, 0x01,  // USAGE_PAGE (Generic Desktop)
	0x09, 0x06,  // USAGE (Keyboard)
	0xA1, 0x01,  // COLLECTION (Application)
	0x05, 0x07,  //   USAGE_PAGE (Keyboard)(Key Codes)
	0x19, 0xE0,  //   USAGE_MINIMUM (Keyboard LeftControl)(224)
	0x29, 0xE7,  //   USAGE_MAXIMUM (Keyboard Right GUI)(231)
	0x15, 0x00,  //   LOGICAL_MINIMUM (0)
	0x25, 0x01,  //   LOGICAL_MAXIMUM (1)
	0x75, 0x01,  //   REPORT_SIZE (1)
	0x95, 0x08,  //   REPORT_COUNT (8)
	0x81, 0x02,  //   INPUT (Data,Var,Abs) ; Modifier byte
	0x95, 0x01,  //   REPORT_COUNT (1)
	0x75, 0x08,  //   REPORT_SIZE (8)
	0x81, 0x03,  //   INPUT (Cnst,Var,Abs) ; Reserved byte
	0x95, 0x05,  //   REPORT_COUNT (5)
	0x75, 0x01,  //   REPORT_SIZE (1)
	0x05, 0x08,  //   USAGE_PAGE (LEDs)
	0x19, 0x01,  //   USAGE_MINIMUM (Num Lock)
	0x29, 0x05,  //   USAGE_MAXIMUM (Kana)
	0x91, 0x02,  //   OUTPUT (Data,Var,Abs) ; LED report
	0x95, 0x01,  //   REPORT_COUNT (1)
	0x75, 0x03,  //   REPORT_SIZE (3)
	0x91, 0x03,  //   OUTPUT (Cnst,Var,Abs) ; LED report padding
	0x95, 0x06,  //   REPORT_COUNT (6)
	0x75, 0x08,  //   REPORT_SIZE (8)
	0x15, 0x00,  //   LOGICAL_MINIMUM (0)
	0x25, 0x65,  //   LOGICAL_MAXIMUM (101)
	0x05, 0x07,  //   USAGE_PAGE (Keyboard)(Key Codes)
	0x19, 0x00,  //   USAGE_MINIMUM (Reserved (no event indicated))(0)
	0x29, 0x65,  //   USAGE_MAXIMUM (Keyboard Application)(101)
	0x81, 0x00,  //   INPUT (Data,Ary,Abs)
	0xC0         // END_COLLECTION
};

// see http://vusb.wikidot.com/driver-api
// constants are found in usbdrv.h
usbMsgLen_t usbFunctionSetup(uint8_t data[8])
{
	usb_hasCommed = 1;

	// see HID1_11.pdf sect 7.2 and http://vusb.wikidot.com/driver-api
	usbRequest_t *rq = (void *)data;

	if ((rq->bmRequestType & USBRQ_TYPE_MASK) != USBRQ_TYPE_CLASS)
		return 0; // ignore request if it's not a class specific request

	// see HID1_11.pdf sect 7.2
	switch (rq->bRequest)
	{
		case USBRQ_HID_GET_IDLE:
			usbMsgPtr = &idle_rate; // send data starting from this byte
			return 1; // send 1 byte
		case USBRQ_HID_SET_IDLE:
			idle_rate = rq->wValue.bytes[1]; // read in idle rate
			return 0; // send nothing
		case USBRQ_HID_GET_PROTOCOL:
			usbMsgPtr = &protocol_version; // send data starting from this byte
			return 1; // send 1 byte
		case USBRQ_HID_SET_PROTOCOL:
			protocol_version = rq->wValue.bytes[1];
			return 0; // send nothing
		case USBRQ_HID_GET_REPORT:
			usbMsgPtr = (uint8_t*)report_buffer; // send the report data
			return 8;
		case USBRQ_HID_SET_REPORT:
			if (rq->wLength.word == 1) // check data is available
			{
				// 1 byte, we don't check report type (it can only be output or feature)
				// we never implemented "feature" reports so it can't be feature
				// so assume "output" reports
				// this means set LED status
				// since it's the only one in the descriptor
				return USB_NO_MSG; // send nothing but call usbFunctionWrite
			}
			else // no data or do not understand data, ignore
			{
				return 0; // send nothing
			}
		default: // do not understand data, ignore
			return 0; // send nothing
	}
}

// see http://vusb.wikidot.com/driver-api
usbMsgLen_t usbFunctionWrite(uint8_t * data, uchar len)
{
	led_state = data[0];
	return 1; // 1 byte read
}

#if defined(__AVR_ATtiny85__) || defined(__AVR_ATtiny45__) || defined(__AVR_ATtiny25__)
/* ------------------------------------------------------------------------- */
/* ------------------------ Oscillator Calibration ------------------------- */
/* ------------------------------------------------------------------------- */
// section copied from EasyLogger
/* Calibrate the RC oscillator to 8.25 MHz. The core clock of 16.5 MHz is
 * derived from the 66 MHz peripheral clock by dividing. Our timing reference
 * is the Start Of Frame signal (a single SE0 bit) available immediately after
 * a USB RESET. We first do a binary search for the OSCCAL value and then
 * optimize this value with a neighboorhod search.
 * This algorithm may also be used to calibrate the RC oscillator directly to
 * 12 MHz (no PLL involved, can therefore be used on almost ALL AVRs), but this
 * is wide outside the spec for the OSCCAL value and the required precision for
 * the 12 MHz clock! Use the RC oscillator calibrated to 12 MHz for
 * experimental purposes only!
 */
void calibrateOscillator(void)
{
    uchar       step = 128;
    uchar       trialValue = 0, optimumValue;
    int         x, optimumDev, targetValue = (unsigned)(1499 * (double)F_CPU / 10.5e6 + 0.5);

    /* do a binary search: */
    do{
        OSCCAL = trialValue + step;
        x = usbMeasureFrameLength();    /* proportional to current real frequency */
        if(x < targetValue)             /* frequency still too low */
            trialValue += step;
        step >>= 1;
    }while(step > 0);
    /* We have a precision of +/- 1 for optimum OSCCAL here */
    /* now do a neighborhood search for optimum value */
    optimumValue = trialValue;
    optimumDev = x; /* this is certainly far away from optimum */
    for(OSCCAL = trialValue - 1; OSCCAL <= trialValue + 1; OSCCAL++){
        x = usbMeasureFrameLength() - targetValue;
        if(x < 0)
            x = -x;
        if(x < optimumDev){
            optimumDev = x;
            optimumValue = OSCCAL;
        }
    }
    OSCCAL = optimumValue;
}
/*
Note: This calibration algorithm may try OSCCAL values of up to 192 even if
the optimum value is far below 192. It may therefore exceed the allowed clock
frequency of the CPU in low voltage designs!
You may replace this search algorithm with any other algorithm you like if
you have additional constraints such as a maximum CPU clock.
For version 5.x RC oscillators (those with a split range of 2x128 steps, e.g.
ATTiny25, ATTiny45, ATTiny85), it may be useful to search for the optimum in
both regions.
*/
#endif

void pressKey(uint8_t modifiers, uint8_t keycode1) {
    report_buffer[0] = modifiers;
    report_buffer[1] = 0;
    report_buffer[2] = keycode1;
    report_buffer[3] = 0;
    report_buffer[4] = 0;
    report_buffer[5] = 0;
    report_buffer[6] = 0;
    report_buffer[7] = 0;
    usbReportSend();
}


void wait(uint32_t millis) {
    while(millis--) {
        usbPoll();
        _delay_ms(1);
    }
}

#include "Light_WS2812/light_ws2812.h"
#include <avr/eeprom.h>

#define CONFIG_LOOP         0x01
#define CONFIG_LOOP_DELAY   0x02

struct cRGB led[1];

char modifiers;
int main() {
    
    led[0].r=120;
    led[0].g=0;
    led[0].b=0;

    ws2812_setleds(led,1);

    usbBegin();
    
    uint8_t byte;
    for(uint16_t i = 0; i < 512; i++) {
        usbPoll();
        
        byte = eeprom_read_byte((uint8_t*)i);

        if(byte > 0xE7) {
            switch(byte) {
                case 0xE8:                          // GOTO
                    i++;                            // Move to next location;
                    i = eeprom_read_word((uint16_t*)i) - 1;    // Jump to new location ((i - 1) + 1);
                    break;

                case 0xE9:                          // WAIT
                    i++;                            
                    wait(eeprom_read_dword((uint32_t*)i));     // Read 4 bytes and wait that amount in ms;
                    i += 3;                         // Move to next bytecode (3 + 1);
                    break;

                case 0xEA:                          // JUMP IF NUM
                    i++;
                    if(led_state & KB_LED_NUM)      // Check numlock state;
                        i = eeprom_read_word((uint16_t*)i) - 1;
                    else
                        i++;
                    break;

                case 0xEB:                          // JUMP IF CAPS
                    i++;
                    if(led_state & KB_LED_CAPS)     
                        i = eeprom_read_word((uint16_t*)i) - 1;
                    else
                        i++;
                    break;

                case 0xEC:                          // JUMP IF SCROLL
                    i++;
                    if(led_state & KB_LED_SCROLL)     
                        i = eeprom_read_word((uint16_t*)i) - 1;
                    else
                        i++;
                    break;
                
                case 0xED:                          // MODON
                    i++;
                    modifiers |= 1 << eeprom_read_byte((uint8_t*)i);
                    break;

                case 0xEE:                          // MODOFF
                    i++;
                    modifiers &= ~( 1 << eeprom_read_byte((uint8_t*)i));
                    break;

                case 0xEF:                          // SHIFT
                    i++;
                    pressKey(modifiers | KEYCODE_MOD_LEFT_SHIFT, eeprom_read_byte((uint8_t*)i));
                    pressKey(0, 0);
                    break;
            }
        }else {
            pressKey(modifiers, byte);
            pressKey(0, 0);
        }
    }

    while(1) usbPoll();

    return 0;
}
