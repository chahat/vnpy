# encoding: UTF-8

'''
This file is only used to store definitions for event type constants.

Since there is no real constant concept in Python, choose to use all-capital variable names instead of constants.
The naming conventions designed here begin with the EVENT_ prefix.

The content of a constant usually selects a string that is representative of the real meaning (for easy understanding).

It is recommended that all constant definitions be placed in this file to make it easier to check for duplicates.
'''
from __future__ import print_function


EVENT_TIMER = 'eTimer'                  # Timer event, sent every 1 second
 


#----------------------------------------------------------------------
def test():
    """Check if there is a constant definition of content duplicates"""
    check_dict = {}
    
    global_dict = globals()    
    
    for key, value in global_dict.items():
        if '__' not in key:                       # Do not check python built-in objects
            if value in check_dict:
                check_dict[value].append(key)
            else:
                check_dict[value] = [key]
            
    for key, value in check_dict.items():
        if len(value)>1:
            print(u'There are duplicate constant definitions:{}'.format(str(key)))
            for name in value:
                print(name)
            print('')
        
    print(u'Test completed')
    

# Run the script directly to test
if __name__ == '__main__':
    test()