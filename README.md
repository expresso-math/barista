# EXPRESSO: Digitizing handwritten equations since 2013.
Work by Josef Lange and Daniel Guilak in fulfillment of University of Puget Sound Computer Science Capstone requirement.

## OpenCV Installation
On Mac OS X Lion, used MacPorts to install OpenCV library -- had to [accept Apple license](http://trac.macports.org/ticket/35337) for XCode first to enable gnuplot to build for some reason with
   
    sudo xcodebuild -license
    
and then installed the OpenCV with

    sudo port selfupdate
    sudo port install opencv +python27
    
per the instructions located on the [OpenCV wiki](http://opencv.willowgarage.com/wiki/Mac_OS_X_OpenCV_Port).
