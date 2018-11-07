#!/usr/bin/env python3
#coding: utf8


"""
Firefox: https://github.com/mozilla/gecko-dev/tree/master/media/ffvpx

cc -I /usr/local/Cellar/ffmpeg/3.0.1/include -Wall -g -c \
        -o avtools.o avtools.c
cc avtools.o -L /usr/local/Cellar/ffmpeg/3.0.1/lib \
        -lavdevice -lavformat -lavfilter -lavcodec \
        -lswresample -lswscale -lavutil  \
        -o avtools

cc aes.h -o aes.o
"""

import os
import re
import sys
import shutil

WORKSPACE_DIR = os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
FFMPEG_SOURCE_DIR = os.path.join(WORKSPACE_DIR, "FFmpeg-n4.0.2")
FFH264_SOURCE_DIR = os.path.join(WORKSPACE_DIR, "ffh264")

def build_ffmpeg_config():
    """
--disable-asm \
--disable-pthreads \
--enable-ffmpeg

./configure \
    --disable-avdevice --disable-filters --disable-programs --disable-doc \
    --disable-swresample --disable-swscale --disable-network \
    --disable-muxers \
    --disable-demuxers \
    --disable-encoders \
    --disable-decoders \
    --disable-parsers \
    --enable-decoder=h264 --enable-parser=h264 --enable-demuxer=h264
"""
    cmd = [
        "./configure",
        "--disable-avdevice", "--disable-filters", "--disable-programs",
        "--disable-doc", "--disable-swresample", "--disable-swscale",
        "--disable-network",
        "--disable-muxers", "--disable-demuxers",
        "--disable-encoders", "--disable-decoders",
        "--disable-parsers",
        "--enable-decoder=h264", "--enable-parser=h264", "--enable-demuxer=h264",
    ]

    if not os.path.exists(os.path.join(FFMPEG_SOURCE_DIR, "config.h")):
        os.system(" ".join(cmd))

def find_h264_decoder_codec_files():
    p = re.compile(r"\#\s*include\s+[\"\'](\S+)[\"\']")
    done = []
    files = [
        os.path.join(FFMPEG_SOURCE_DIR, "libavcodec/h264dec.h"),
        os.path.join(FFMPEG_SOURCE_DIR, "libavcodec/h264dec.c"),
    ]
    c_files = [  ]

    def search(filepath, done):
        filecontent = open(filepath, "r").read()
        done.append(filepath)
        for include in p.findall(filecontent):
            if include == "config.h" or include == "mfx/mfxvp8.h":
                continue
            
            if include.startswith("libav") or include.startswith("compat") and "/" in include:
                include_file_path = os.path.join(FFMPEG_SOURCE_DIR, include)
            else:
                path = filepath.replace(FFMPEG_SOURCE_DIR+"/", "")
                dirname = os.path.split(path)[0]
                include_file_path = os.path.join(FFMPEG_SOURCE_DIR, dirname, include)
            
            if include_file_path not in done:
                search(include_file_path, done)
            
            if include_file_path.endswith(".h"):
                c_file = include_file_path[:-2] + ".c"
                if os.path.exists(c_file) and os.path.isfile(c_file):
                    if c_file not in done:
                        search(c_file, done)

    for f in files:
        search(f, done)

    # for filename in os.listdir(os.path.join(FFMPEG_SOURCE_DIR, "libavcodec")):
    #     filepath = os.path.join(FFMPEG_SOURCE_DIR, "libavcodec", filename)
    #     if "h264" in filename and os.path.isfile(filepath):
    #         if filepath not in done:
    #             search(filepath, done)

    done = list(set(done))
    done.sort()

    return done
    

def copy_ffmpeg_decoder_files(files):
    os.chdir(FFH264_SOURCE_DIR)

    for filepath in files:
        path = filepath.replace(FFMPEG_SOURCE_DIR+"/", "")

        src = filepath
        dst_path, dst_file = os.path.split(path)
        dst_path = os.path.join(FFH264_SOURCE_DIR, dst_path)

        if not os.path.exists(dst_path):
            os.makedirs(dst_path)

        assert(os.path.isdir(dst_path))

        dst = os.path.join(FFH264_SOURCE_DIR, path)
        
        print("copy %s -> %s" % (src, dst) )

        shutil.copy(src, dst)

    print("files: %d" % len(files))
    os.chdir(FFMPEG_SOURCE_DIR)

    # FFMPEG config.h
    shutil.copy(os.path.join(FFMPEG_SOURCE_DIR, "config.h"), os.path.join(FFH264_SOURCE_DIR, "config.h"))
    shutil.copy(os.path.join(FFMPEG_SOURCE_DIR, "config.asm"), os.path.join(FFH264_SOURCE_DIR, "config.asm"))


def build():
    print("WorkSpace dir: %s" % WORKSPACE_DIR)
    build_ffmpeg_config()
    
    files = find_h264_decoder_codec_files()
    copy_ffmpeg_decoder_files(files)


def main():
    build()


if __name__ == '__main__':
    main()