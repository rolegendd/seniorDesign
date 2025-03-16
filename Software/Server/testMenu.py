#!/usr/bin/env python3
def submenu():
    while True:
        print("\nSub-Menu")
        print("1. Sub-option 1")
        print("2. Sub-option 2")
        print("3. Go back")

        choice = input("Enter your choice: ")

        match choice:
            case "1":
                print("You selected Sub-option 1.")
            case "2":
                print("You selected Sub-option 2.")
            case "3":
                print("Returning to Main Menu...")
                return  # Return to previous menu 
            case _:
                print("Invalid choice. Please try again.")

def main_menu():
    while True:
        print("\nMain Menu")
        print("1. Go to Sub-Menu")
        print("2. Exit")

        choice = input("Enter your choice: ")

        match choice:
            case "1":
                submenu()  # Enter the sub-menu
            case "2":
                print("Exiting program...")
                break
            case _:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()

