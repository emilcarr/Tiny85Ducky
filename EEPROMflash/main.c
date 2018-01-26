#include <avr/eeprom.h>
#include "Light_WS2812/light_ws2812.h"
#include "program.h"

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
