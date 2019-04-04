import sqlite3
import numpy as np
import scipy.stats
import matplotlib.pyplot
import time
from mpl_toolkits import mplot3d

conn_r = sqlite3.connect("05762139.sqlite3")
c_r = conn_r.cursor()

c_r.execute("SELECT DISTINCT a.time FROM lis_data a INNER JOIN lis_data b ON a.time = b.time WHERE a.lab_test_name='CREA' AND b.lab_test_name='K';")
t = c_r.fetchall()

cr = []
k = []

for x in t:
    c_r.execute("SELECT lab_value FROM lis_data WHERE time=(?) AND lab_test_name='CREA'", (x[0],))
    j = c_r.fetchone()
    cr.append(j[0])

for x in t:
    c_r.execute("SELECT lab_value FROM lis_data WHERE time=(?) AND lab_test_name='K'", (x[0],))
    j = c_r.fetchone()
    k.append(j[0])

# Linear regression
cr = np.array(cr).astype(np.float)
k = np.array(k).astype(np.float)
t = [time.mktime(time.strptime(i[0], "%Y/%m/%d %H:%M:%S")) for i in t]
slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(cr, k)
print(scipy.stats.describe(cr))
print(scipy.stats.describe(k))
print(slope, intercept, r_value, p_value, std_err)
print(r_value ** 2)

# Plotting
#matplotlib.pyplot.plot(cr, k, 'ro')
#matplotlib.pyplot.axis(xmin=0,xmax=8,ymin=0,ymax=8)
#matplotlib.pyplot.xlabel("Cr")
#matplotlib.pyplot.ylabel("K")
#matplotlib.pyplot.grid()
#matplotlib.pyplot.show()

ax = matplotlib.pyplot.axes(projection='3d')
ax.plot3D(cr, k, t, 'green')
matplotlib.pyplot.xlabel("Cr")
matplotlib.pyplot.ylabel("K")
matplotlib.pyplot.grid()
matplotlib.pyplot.show()