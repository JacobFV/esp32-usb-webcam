if(${IDF_VERSION_MAJOR} LESS 6)
    set(usb_requires usb)
else()
    set(usb_requires esp_hw_support)
endif()

idf_component_register(SRCS usb_device_uvc.c tusb/usb_descriptors.c
                    INCLUDE_DIRS "include"
                    REQUIRES ${usb_requires} esp_timer)

target_compile_definitions(${COMPONENT_LIB} PUBLIC
    USB_DEVICE_UVC_VER_MAJOR=1
    USB_DEVICE_UVC_VER_MINOR=3
    USB_DEVICE_UVC_VER_PATCH=0
)

idf_component_get_property(tusb_lib espressif__tinyusb COMPONENT_LIB)

target_include_directories(${tusb_lib} PUBLIC "${COMPONENT_DIR}/tusb")
