#include <usb.h>
#include <stdio.h>
#include <string.h>

// Get descriptor string of given device, with given index, language and output to given buffer.
static int usbGetDescriptorString(usb_dev_handle *dev, int index, int langid, char *outBuffer, int bufferLength) {
    char buffer[256];
    int rval, i;

    // make standard GET_DESCRIPTOR request
    rval = usb_control_msg(dev, USB_TYPE_STANDARD | USB_RECIP_DEVICE | USB_ENDPOINT_IN, USB_REQ_GET_DESCRIPTOR, (USB_DT_STRING << 8) + index, langid, buffer, sizeof(buffer), 1000);
    if (rval < 0)   // Error
        return rval;

    // rval is response size. buffer[0] is string size.
    if((unsigned char)buffer[0] < rval) // string is shorter than bytes read
        rval = (unsigned char)buffer[0];
    
    if(buffer[1] != USB_DT_STRING) // Second byte is Data Type.
        return 0; // Invalid return type

    rval /= 2;  // UTF-16LE chars are half of rval.

    // Convert to ASCII
    for(i = 1; i < rval && i < bufferLength; i++) { // index 0 is not data
        if(buffer[2*i + 1] == 0) // only 8 bits of 16-bit utf-16le chars are used.
            outBuffer[i - 1] = buffer[2*i];
        else
            outBuffer[i - 1] = '?'; // out of ASCII range
    }
    outBuffer[i-1] = 0;

    return i - 1;
}

static usb_dev_handle * usbOpenDevice(int vendorID, int productID, char *productVendor) {
    struct usb_bus *bus;
    struct usb_device *dev;
    char devProduct[256];
    usb_dev_handle *handle = NULL;

    usb_init();         // Initialise USB and find devices
    usb_find_busses();
    usb_find_devices();

    for(bus = usb_get_busses(); bus; bus = bus->next) { // iterate through USB buses and their attached devices
        for(dev = bus->devices; dev; dev = dev->next) {
            if((dev->descriptor.idVendor != vendorID) | (dev->descriptor.idProduct != productID))   // this is not our device
                continue;

            if(!(handle = usb_open(dev))) {  // Open the device and check if it was unsuccessful
                fprintf(stderr, "WARNING: Cannot open USB device: %s\n", usb_strerror());
                continue;
            }
            
            // Get the USB vendor name in english.
            if(usbGetDescriptorString(handle, dev->descriptor.iManufacturer, 0x0409, devProduct, sizeof(devProduct)) < 0) {
                fprintf(stderr, "WARNING: Cannot query product for device: %s\n", usb_strerror());
                usb_close(handle);
                continue;
            }
            
            printf("Found USB Device %s\n", devProduct);

             if(strcmp(devProduct, productVendor) == 0)
                return handle;
            else
                usb_close(handle);
        }
    }

    return NULL;
}

#define USBRQ_LED_BLUE 0x0E
#define USBRQ_LED_RED 0x0F

int main(int argc, char **argv) {
    usb_dev_handle *handle = NULL;

    handle = usbOpenDevice(0x16c0, 0x27db, "Generic");

    if(handle == NULL) {
        fprintf(stderr, "Could not find USB device!\n");
        exit(1);
    }

    int rval = 0;
    char buffer[256];
    //rval = usb_control_msg(handle, USB_TYPE_VENDOR | USB_RECIP_DEVICE | USB_ENDPOINT_IN, USBRQ_LED_BLUE, 0, 0, (char *)buffer, sizeof(buffer), 5000);
    
    rval = usb_control_msg(handle, USB_TYPE_VENDOR | USB_RECIP_DEVICE | USB_ENDPOINT_IN, 0x09, 0x0200, 0x0000, (char* )buffer, 1, 5000);

    if (rval < 0)
        fprintf(stderr, "USB error: %s\n", usb_strerror());
    else
        printf("Got %d bytes: %s\n", rval, buffer);
    
    usb_close(handle);
}
