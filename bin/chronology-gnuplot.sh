#! /usr/bin/gnuplot -c

reset session

if (ARG2 eq "qt") {
  set terminal qt
} else if (ARG2 eq "svg") {
  # set terminal svg size 900 600 background rgbcolor("white") font "Arial,12"
  set terminal svg size 900 600 font "Arial,14"
}
set encoding utf8
set datafile separator comma
set timefmt "%Y-%m"
set xdata time

thismonth = system('date +%Y-%m')
set xrange ["1990-01":thismonth]

year = 365.25 * 86400
set style fill solid  # solid color boxes
set xtics "1990-01", 2*year, thismonth
# set xtics 4*year
set xtics format "%Y" nomirror rotate by 90 offset 0,-1.5 # rotate by 45 offset -3,-1
set mxtics 2
set ytics nomirror
set autoscale xfix
set rmargin 0 # Makes currently active orgs touch the right end
set lmargin at screen 0.25
set border 3 # bottom and left


myBoxWidth = 0.4
set offsets 0,0,0.5-myBoxWidth/2.,0.5

set label "backyard" at graph "1990-01",1
# set arrow from "2010-01",-myBoxWidth to "2010-01",-28+myBoxWidth nohead dashtype 2
set grid xtics noytics
# using x:y:xmin:xmax:ymin:xmax:color:ytic(N)
# x = (0) = always zero
# y = (-$1) = negated value of column one, which is the desired index
# xmin = (timecolumn(3)) = column 3 parsed with timefmt
# xmax = (timecolumn(4)) = column 4 parsed with timefmt
# ymin = (-$1-myBoxWidth/2.) = centered along the negative index number, minus a thickness value
# ymax = (-$1-myBoxWidth/2.) = centering, plus thickness value
# ytic(2) = use text column 2 for tic values instead of y
# with boxxy[error] = plot boxes
# lc [linecolor] var[iable] = use next column specifier for color index. This is the :5 part.
# notitle = don't add to legend
plot ARG1 using (0):(-$1):(timecolumn(3)):(timecolumn(4)):(-$1-myBoxWidth/2.):(-$1+myBoxWidth/2.):5:ytic(2) \
     with boxxy lc var notitle


if (ARG2 eq "qt") {
  pause -1 "Hit enter to continue"
}
