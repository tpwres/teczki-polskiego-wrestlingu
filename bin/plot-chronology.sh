#! /usr/bin/gnuplot -c

reset session

if (ARG1 eq "qt") {
  set terminal qt
} else if (ARG1 eq "svg") {
  set terminal svg size 900 600 background rgbcolor("white") font "Arial,12"
}
set encoding utf8
set datafile separator comma
set timefmt "%Y-%m"
set xdata time

set xrange ["1990-01":*]
set style fill solid  # solid color boxes
set xtics "1990-01", 2*365.25*86400, "2024-12"
set xtics format "%Y" nomirror
set ytics nomirror
set autoscale xfix
# unset key             # turn off all titles
set border 3 # bottom and left


myBoxWidth = 0.4
set offsets 0,0,0.5-myBoxWidth/2.,0.5

set label "backyard" at graph "1990-01",1
# using x:y:xmin:xmax:ymin:xmax:color:ytic(N)
# x = (0) = always zero
# y = (-$1) = negated value of column one, which is the desired index
# xmin = (timecolumn(3)) = column 3 parsed with timefmt
# xmax = (timecolumn(4)) = column 4 parsed with timefmt
# ymin = (-$1-myBoxWidth/2.) = centered along the negative index number, minus a thickness value
# ymax = (-$1-myBoxWidth/2.) = centering, plus thickness value
# ytic(2) = use text column 2 for tic values instead of y
plot '/dev/stdin' using (0):(-$1):(timecolumn(3)):(timecolumn(4)):(-$1-myBoxWidth/2.):(-$1+myBoxWidth/2.):5:ytic(2) with boxxy \
     lc var notitle

if (ARG1 eq "qt") {
  pause -1 "Hit enter to continue"
}