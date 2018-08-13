#!/usr/bin/env python2
# -*- coding: utf-8 -*-


# Copyright 2010, 2011 Michael Ossmann
# Copyright 2015 Travis Goodspeed
#
# This file was forked from Project Ubertooth as a DFU client for the
# TYT MD380, an amateur radio for the DMR protocol on the UHF bands.
# This script implements a lot of poorly understood extensions unique
# to the MD380.
#
#
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.

# http://pyusb.sourceforge.net/docs/1.0/tutorial.html
from __future__ import print_function

import sys
import time

import usb.core

import dfu_suffix
from DFU import DFU, State, Enumeration

# The tricky thing is that *THREE* different applications all show up
# as this same VID/PID pair.
#
# 1. The Tytera application image.
# 2. The Tytera bootloader at 0x08000000
# 3. The mask-rom bootloader from the STM32F405.
md380_vendor = 0x0483
md380_product = 0xdf11


# application_offset = 0x08000000
# ram_offset = 0x20000000
# application_size   = 0x00040000


def download(dfu, data, flash_address):
    block_size = 1 << 8
    sector_size = 1 << 12
    if flash_address & (sector_size - 1) != 0:
        raise Exception('Download must start at flash sector boundary')

    block_number = flash_address / block_size
    assert block_number * block_size == flash_address

    try:
        while len(data) > 0:
            packet, data = data[:block_size], data[block_size:]
            if len(packet) < block_size:
                packet += '\xFF' * (block_size - len(packet))
            dfu.download(block_number, packet)
            status, timeout, state, discarded = dfu.get_status()
            sys.stdout.write('.')
            sys.stdout.flush()
            block_number += 1
    finally:
        print()

class RadioModels(Enumeration):
    map = {
        0: 'MD380',
        1: 'MD2017',
    }
RadioModels.create_from_map()

def download_codeplug(dfu, data):
    """Downloads a codeplug to the MD380."""
    block_size = 1024
    dfu.wait_till_ready()

    dfu.md380_custom(0x91, 0x01)  # Programming Mode
    dfu.md380_custom(0x91, 0x01)  # Programming Mode
    radioid = dfu.identify_radio() #0xa2 0x01
    if radioid[0:4] == "2017":
        thisradio=RadioModels.MD2017
    else:
        thisradio=RadioModels.MD380
    time.sleep(2)
    dfu.md380_custom(0xa2, 0x02)
    hexdump(dfu.get_command())  # Gets a string.
    dfu.md380_custom(0xa2, 0x03)
    hexdump(dfu.get_command())  # Gets a string.
    dfu.md380_custom(0xa2, 0x04)
    hexdump(dfu.get_command())  # Gets a string.
    dfu.md380_custom(0xa2, 0x07)
    hexdump(dfu.get_command())  # Gets a string.
    """ 
    sudo modprobe usbmon, wireshark-gtk, !(frame.len == 64) && usb.src == "host"
    MD-2017
    ✔    9101
    ✔    9101
    ✔    a201
    ✔    a202
    ✔    a203
    ✔    a204
    ✔    a207
    ✔    41:00:00:00:00
    ✔    41:00:00:01:00
    ✔    41:00:00:02:00
    ✔    41:00:00:03:00
    ✔    41:00:00:11:00
    ✔    41:00:00:12:00
    ✔    41:00:00:13:00
    ✔    41:00:00:14:00
    ✔    41:00:00:15:00
    ✔    41:00:00:16:00
    ✔    41:00:00:17:00
    ✔    41:00:00:18:00
    ✔    41:00:00:19:00
    ✔    21:00:00:00:00
    ✔    start copying
        after wValue == 0x41
        21:00:00:01:00, wValue = 2
        after wValue == 0x41
        21:00:00:02:00, wValue = 2
    rpt
    debug notes:
        249 not accurate for MD2017? Shifted 16 bytes starting at 0x40235

    """

    dfu.erase_block(0x00000000,True)
    dfu.erase_block(0x00010000,True)
    dfu.erase_block(0x00020000,True)
    dfu.erase_block(0x00030000,True)
    if thisradio == RadioModels.MD2017:
        dfu.erase_block(0x00110000,True)
        dfu.erase_block(0x00120000,True)
        dfu.erase_block(0x00130000,True)
        dfu.erase_block(0x00140000,True)
        dfu.erase_block(0x00150000,True)
        dfu.erase_block(0x00160000,True)
        dfu.erase_block(0x00170000,True)
        dfu.erase_block(0x00180000,True)
        dfu.erase_block(0x00190000,True)
        addr_multiplier = 0
        
    dfu.set_address(0x00000000)  # Zero address, used by configuration tool.

    status, timeout, state, discarded = dfu.get_status()
    #print(status, timeout, state, discarded)

    block_number = 2
    next_set = False
    print("sending %d bytes, %f blocks"%(len(data),len(data)/block_size))

    try:
        while len(data) > 0:
            packet, data = data[:block_size], data[block_size:]
            if len(packet) < block_size:
                packet += '\xFF' * (block_size - len(packet))
            dfu.download(block_number, packet)
            dfu.wait_till_ready()
            #state = 11
            #while state != State.dfuDNLOAD_IDLE:
            #    status, timeout, state, discarded = dfu.get_status()
                #print(status, timeout, state, discarded)
            sys.stdout.write('.')
            sys.stdout.flush()
            block_number += 1
            if thisradio == RadioModels.MD2017 and block_number == 0x42:
                #set pointer to same blocks we erased above
                block_number = 2
                addr_multiplier += 1
                if addr_multiplier > 3 and not next_set:
                    next_set = True
                    addr_multiplier = 1
                    data = data[16:] #skip 16 bytes to solve alignment issues - not sure why, this is just what the captures show
                offset = 0 if not next_set else 0x100000  
                if addr_multiplier > 9: print("Done!"); break
                dfu.set_address(0x00000000 + offset +0x10000  * addr_multiplier, True)
                print()
    finally:
        print()
        dfu.md380_reboot()


def hexdump(string):
    """God awful hex dump function for testing."""
    buf = ""
    i = 0
    for c in string:
        buf += "%02x" % c
        i += 1
        if i & 3 == 0:
            buf += " "
        if i & 0xf == 0:
            buf += "   "
        if i & 0x1f == 0:
            buf += "\n"

    print(buf)


def upload_bootloader(dfu, filename):
    """Dumps the bootloader, but only on Mac."""
    # dfu.set_address(0x00000000); # Address is ignored, so it doesn't really matter.

    # Bootloader stretches from 0x08000000 to 0x0800C000, but our
    # address and block number are ignored, so we set the block size
    # ot 0xC000 to yank the entire thing in one go.  The application
    # comes later, I think.
    block_size = 0xC000  # 0xC000;

    f = None
    if filename is not None:
        f = open(filename, 'wb')

    print("Dumping bootloader.  This only works in radio mode, not programming mode.")
    try:
        data = dfu.upload(2, block_size)
        status, timeout, state, discarded = dfu.get_status()
        if len(data) == block_size:
            print("Got it all!")
        else:
            print("Only got %i bytes.  Older versions would give it all." % len(data))
            # raise Exception('Upload failed to read full block.  Got %i bytes.' % len(data))
        if f is not None:
            f.write(data)
        else:
            hexdump(data)

    finally:
        print("Done.")


def upload_codeplug(dfu, filename):
    """Uploads a codeplug from the radio to the host."""
    dfu.md380_custom(0x91, 0x01)  # Programming Mode
    # dfu.md380_custom(0xa2,0x01); #Returns "DR780...", seems to crash client.
    # hexdump(dfu.get_command());  #Gets a string.
    dfu.md380_custom(0xa2, 0x02)
    dfu.md380_custom(0xa2, 0x02)
    dfu.md380_custom(0xa2, 0x03)
    dfu.md380_custom(0xa2, 0x04)
    dfu.md380_custom(0xa2, 0x07)

    dfu.set_address(0x00000000)  # Zero address, used by configuration tool.

    f = open(filename, 'wb')
    block_size = 1024
    try:
        # Codeplug region is 0 to 3ffffff, but only the first 256k are used.
        for block_number in range(2, 0x102):
            data = dfu.upload(block_number, block_size)
            status, timeout, state, discarded = dfu.get_status()
            # print("Status is: %x %x %x %x" % (status, timeout, state, discarded))
            sys.stdout.write('.')
            sys.stdout.flush()
            if len(data) == block_size:
                f.write(data)
                # hexdump(data);
            else:
                raise Exception('Upload failed to read full block.  Got %i bytes.' % len(data))
                # dfu.md380_reboot()
    finally:
        print("Done.")

def upload_codeplug_md2017(dfu, filename):
    """Uploads a codeplug from the radio to the host."""
    dfu.md380_custom(0x91, 0x01)  # Programming Mode
    # dfu.md380_custom(0xa2,0x01); #Returns "DR780...", seems to crash client.
    # hexdump(dfu.get_command());  #Gets a string.
    dfu.md380_custom(0xa2, 0x02)
    dfu.md380_custom(0xa2, 0x02)
    dfu.md380_custom(0xa2, 0x03)
    dfu.md380_custom(0xa2, 0x04)
    dfu.md380_custom(0xa2, 0x07)

    dfu.set_address(0x00000000)  # Zero address, used by configuration tool.

    tmpDfu = "" #temp buffer for CRC calculation
    f = open(filename, 'wb')
    block_size = 1024
    try:
        # Codeplug region is 0 to 3ffffff, but only the first 256k are used.
        for block_number in range(2, 0x102):
            data = dfu.upload(block_number, block_size)
            status, timeout, state, discarded = dfu.get_status()
            # print("Status is: %x %x %x %x" % (status, timeout, state, discarded))
            sys.stdout.write('.')
            sys.stdout.flush()
            if len(data) == block_size:
                f.write(data)
                for i in data:
                    tmpDfu = tmpDfu + chr(i)
                # hexdump(data);
            else:
                raise Exception('Upload failed to read full block.  Got %i bytes.' % len(data))
                # dfu.md380_reboot()
        sys.stdout.write('Finished first part. Adding dummy-DFU-Suffix.\n')
        sys.stdout.flush()
        suffix = [ 0x00, # bcdDevice lo ?
        0x02, # bcdDevice hi ?
        0x11, # idProductLo (OK)
        0xDF, # idProductHi (OK)
        0x83, # idVendor lo (OK)
        0x04, # idVendor hi (OK)
        0x1A, # bcdDFU field, fixed to 0x011A
        0x01, # second byte
        0x55, # DfuSignature: "UFD" char 1
        0x46, # DfuSignature: "UFD" char 2
        0x44, # DfuSignature: "UFD" char 3
        0x10, # Length of suffix 16
        0x12, # CRC Byte 1 -> TODO: how to calculate?
        0x71, # CRC Byte 2 
        0x65, # CRC Byte 3 
        0x8E] # CRC Byte 4 
        for x in suffix:
            f.write(chr(x))
        dfu.set_address(0x00110000, True)
        for block_number in range(2, 0x242):
            data = dfu.upload(block_number, block_size)
            status, timeout, state, discarded = dfu.get_status()
            # print("Status is: %x %x %x %x" % (status, timeout, state, discarded))
            sys.stdout.write('.')
            sys.stdout.flush()
            if len(data) == block_size:
                f.write(data)
                # hexdump(data);
            else:
                raise Exception('Upload failed to read full block.  Got %i bytes.' % len(data))
                # dfu.md380_reboot()
    finally:
        print("Done.")

def download_firmware(dfu, data):
    """ Download new firmware binary to the radio. """
    addresses = [
        0x0800c000,
        0x08010000,
        0x08020000,
        0x08040000,
        0x08060000,
        0x08080000,
        0x080a0000,
        0x080c0000,
        0x080e0000]
    sizes = [0x4000,  # 0c
             0x10000,  # 1
             0x20000,  # 2
             0x20000,  # 4
             0x20000,  # 6
             0x20000,  # 8
             0x20000,  # a
             0x20000,  # c
             0x20000]  # e
    block_ends = [0x11, 0x41, 0x81, 0x81, 0x81, 0x81, 0x81, 0x81, 0x81]
    try:
        # Are we in the right mode?
        mfg = dfu.get_string(1)
        if mfg != u'AnyRoad Technology':
            print("""ERROR: You forgot to enter the bootloader.
Please hold PTT and the button above it while rebooting.  You
should see the LED blinking green and red, and then your
radio will be radio to accept this firmware update.""")
            sys.exit(1)

        print("Beginning firmware upgrade.")
        sys.stdout.flush() # let text appear immediately (for mingw)
        status, timeout, state, discarded = dfu.get_status()
        assert state == State.dfuIDLE

        dfu.md380_custom(0x91, 0x01)
        dfu.md380_custom(0x91, 0x31)

        for address in addresses:
            if dfu.verbose:
                print("Erasing address@ 0x%x" % address)
                sys.stdout.flush()
            dfu.erase_block(address)

        block_size = 1024
        block_start = 2
        address_idx = 0

        if data[0:14] == "OutSecurityBin":  # skip header if present
            if dfu.verbose:
                print("Skipping 0x100 byte header in data file")
            header, data = data[:0x100], data[0x100:]

        print("Writing firmware:")

        assert len(addresses) == len(sizes)
        numaddresses = len(addresses)

        while address_idx < numaddresses:  # for each section
            print("%0d%% complete" % (address_idx * 100 / numaddresses))
            sys.stdout.flush() # let text appear immediately (for mingw)
            address = addresses[address_idx]
            size = sizes[address_idx]
            dfu.set_address(address)

            if address_idx != len(addresses) - 1:
                assert address + size == addresses[address_idx + 1]

            datawritten = 0
            block_number = block_start

            while len(data) > 0 and size > datawritten:  # for each block
                assert block_number <= block_ends[address_idx]
                packet, data = data[:block_size], data[block_size:]

                if len(packet) < block_size:
                    packet += '\xFF' * (block_size - len(packet))

                dfu.download(block_number, packet)
                dfu.wait_till_ready()

                datawritten += len(packet)
                block_number += 1
                # if dfu.verbose: sys.stdout.write('.'); sys.stdout.flush()
            # if dfu.verbose: sys.stdout.write('_\n'); sys.stdout.flush()
            address_idx += 1
        print("100% complete, now safe to disconnect and/or reboot radio")
    except Exception as e:
        print(e)


def upload(dfu, flash_address, length, path):
    # block_size = 1 << 8
    block_size = 1 << 14

    print("Address: 0x%08x" % flash_address)
    print("Block Size:    0x%04x" % block_size)

    if flash_address & (block_size - 1) != 0:
        raise Exception('Upload must start at block boundary')

    block_number = flash_address / block_size
    assert block_number * block_size == flash_address
    # block_number=0x8000;
    print("Block Number:    0x%04x" % block_number)

    cmds = dfu.get_command()
    print("%i supported commands." % len(cmds))
    for cmd in cmds:
        print("Command %02x is supported by UPLOAD." % cmd)

    dfu.set_address(0x08001000)  # RAM
    block_number = 2

    f = open(path, 'wb')

    try:
        while length > 0:
            data = dfu.upload(block_number, block_size)
            status, timeout, state, discarded = dfu.get_status()
            print("Status is: %x %x %x %x" % (status, timeout, state, discarded))
            sys.stdout.write('.')
            sys.stdout.flush()
            if len(data) == block_size:
                f.write(data)
            else:
                raise Exception('Upload failed to read full block.  Got %i bytes.' % len(data))
            block_number += 1
            length -= len(data)
    finally:
        f.close()
        print()


def detach(dfu):
    if dfu.get_state() == State.dfuIDLE:
        dfu.detach()
        print('Detached')
    else:
        print('In unexpected state: %s' % dfu.get_state())


def init_dfu(alt=0):
    dev = usb.core.find(idVendor=md380_vendor,
                        idProduct=md380_product)

    if dev is None:
        raise RuntimeError('Device not found')
    dfu = DFU(dev, alt)
    dev.default_timeout = 3000

    try:
        dfu.enter_dfu_mode()
    except usb.core.USBError as e:
        if len(e.args) > 0 and e.args[0] == 'Pipe error':
            raise RuntimeError('Failed to enter DFU mode. Is bootloader running?')
        else:
            raise e

    return dfu


def usage():
    print("""
Usage: md380-dfu <command> <arguments>

Write a codeplug to the radio. Supported file types: RDT (from official Tytera editor), DFU (with suffix) and raw binaries
    md380-dfu write <codeplug.rdt>
    md380-dfu write <codeplug.dfu>
    md380-dfu write <codeplug.bin>

Write firmware to the radio.
    md380-dfu upgrade <firmware.bin>

Read a codeplug and write it to a file.
    md380-dfu read <codeplug.bin>

Read a MD-2ß17 codeplug and write it to a file.
    md380-dfu readmd2017 <codeplug.bin>

Dump the bootloader from Flash memory.
    md380-dfu readboot <filename.bin>


Print the time from the MD380.
    md380-dfu time

Set time and date on MD380 to system time or specified time.
    md380-dfu settime
    md380-dfu settime "mm/dd/yyyy HH:MM:SS" (with quotes)

Detach the bootloader and execute the application firmware:
    md380-dfu detach

Close the bootloader session.
    md380-dfu reboot


Upgrade to new firmware:
    md380-dfu upgrade foo.bin
""")


def main():
    try:
        if len(sys.argv) == 3:
            if sys.argv[1] == 'read':
                import usb.core
                dfu = init_dfu()
                upload_codeplug(dfu, sys.argv[2])
                print('Read complete')
            elif sys.argv[1] == 'readmd2017':
                import usb.core
                dfu = init_dfu()
                upload_codeplug_md2017(dfu, sys.argv[2])
                print('Read complete')
            elif sys.argv[1] == 'readboot':
                print("This only works from OS X.  Use the one in md380-tool with patched firmware for other bootloaders.")
                import usb.core
                dfu = init_dfu()
                upload_bootloader(dfu, sys.argv[2])

            elif sys.argv[1] == "upgrade":
                import usb.core
                with open(sys.argv[2], 'rb') as f:
                    data = f.read()
                    dfu = init_dfu()
                    download_firmware(dfu, data)

            elif sys.argv[1] == 'write':
                import usb.core
                f = open(sys.argv[2], 'rb')
                data = f.read()
                f.close()
                print(len(data),data[0:5])

                if sys.argv[2][-4:] == '.dfu':
                    suf_len, vendor, product = dfu_suffix.check_suffix(data)
                    dfu = init_dfu()
                    codeplug = data[:-suf_len]
                elif sys.argv[2][-4:] == '.rdt' and ( len(data) == 262709 or len(data) == 852533 ) and data[0:5] == 'DfuSe':
                    #small is md380 codeplug, large is MD2017
                    dfu = init_dfu()
                    codeplug = data[549:len(data) - 16]
                else:
                    dfu = init_dfu()
                    codeplug = data

                download_codeplug(dfu, codeplug)
                print('Write complete')

            elif sys.argv[1] == 'sign':
                filename = sys.argv[2]

                f = open(filename, 'rb')
                firmware = f.read()
                f.close()

                data = dfu_suffix.add_suffix(firmware, md380_vendor, md380_product)

                dfu_file = filename[:-4] + '.dfu'
                f = open(dfu_file, 'wb')
                f.write(data)
                f.close()
                print("Signed file written: %s" % dfu_file)

            elif sys.argv[1] == 'settime':
                import usb.core
                dfu = init_dfu()
                dfu.set_time()
            else:
                usage()

        elif len(sys.argv) == 2:
            if sys.argv[1] == 'detach':
                import usb.core
                dfu = init_dfu()
                dfu.set_address(0x08000000)  # Radio Application
                detach(dfu)
            elif sys.argv[1] == 'time':
                import usb.core
                dfu = init_dfu()
                print(dfu.get_time())
            elif sys.argv[1] == 'settime':
                import usb.core
                dfu = init_dfu()
                dfu.set_time()
            elif sys.argv[1] == 'reboot':
                import usb.core
                dfu = init_dfu()
                dfu.md380_custom(0x91, 0x01)  # Programming Mode
                dfu.md380_custom(0x91, 0x01)  # Programming Mode
                # dfu.md380_custom(0x91,0x01); #Programming Mode
                # dfu.drawtext("Rebooting",160,50);
                dfu.md380_reboot()
            elif sys.argv[1] == 'abort':
                import usb.core
                dfu = init_dfu()
                dfu.abort()
            elif sys.argv[1] == "ident":
                dfu = init_dfu()
                import binascii
                rid = dfu.identify_radio()
                print(binascii.hexlify(rid))
                print(rid)
            else:
                usage()
        else:
            usage()
    except RuntimeError as e:
        print(e.args[0])
        exit(1)
    except Exception as e:
        print(e)
        # print(dfu.get_status())
        exit(1)


if __name__ == '__main__':
    main()
