#!/bin/bash

while true; do
  echo -e "\nMenu: "
  echo "1: Display current date and time"
  echo "2: Show list of files in current directory"
  echo "3: Display current working directory"
  echo "4: Exit the script"

  read -p "Enter your choice: " choice

  case $choice in
    1) date ;;
    2) ls ;;
    3) pwd ;;
    4) echo "Exiting script"; exit 0 ;;
    *) echo "Invalid choice :(" ;;
  esac 
done

