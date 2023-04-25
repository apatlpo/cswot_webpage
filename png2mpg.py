# this script should not necessary as make_movies.py should already perform this task

from subprocess import check_output, STDOUT

for e in ["large", "south", "central", "north"]:

    com = f'''ffmpeg -framerate 10 -pattern_type glob -i 'figs_{e}/*.png' -c:v libx264 -pix_fmt yuv420p cswot_{e}.mp4'''
    print(com)
    output = check_output(com, shell=True, stderr=STDOUT, universal_newlines=True).rstrip('\n')
    print(output)

