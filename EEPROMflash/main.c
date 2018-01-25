#include <avr/eeprom.h>
#include "Light_WS2812/light_ws2812.h"

#define PROGSIZE 29
uint8_t PROG[PROGSIZE] = {  0xe9, 0xe8, 0x03, 0x00, 0x00, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0xef, 0x04, 0xef, 0x05,
                            0xef, 0x06, 0xef, 0x07, 0xef, 0x08, 0xef, 0x09, 0xef, 0x0a, 0xe8, 0x00, 0x00                    };

struct cRGB led[1];

int main() {
    
    led[0].r=120;
    led[0].g=0;
    led[0].b=0;
    ws2812_setleds(led, 1);

    for(int i = 0; i < PROGSIZE; i++)
        eeprom_write_byte((uint8_t*) i, PROG[i]);
    
    led[0].r=0;
    led[0].g=120;
    led[0].b=0;
    ws2812_setleds(led, 1);


    while(1);

    return 0;
}
