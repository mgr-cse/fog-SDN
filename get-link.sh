#!/bin/bash

echo $(ip link | awk '{print $2}' | grep "^h")