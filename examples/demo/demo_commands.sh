
# Define the list of commands that will be shown by the demo
commands=(
    'tulp write a python program that say \"Welcome to tulp AI driven CLI\", using one different color per letter | python'
    "echo \"Natural language to plot:\""
    'tulp write a python program that plots 1,1 2,2 3,3 with the leyend tulp line using mathplotlib | python'
    "echo \"Now let's see how data extraction works:\""
    'cat ../oranges_poem.txt'
    'cat ../oranges_poem.txt | tulp write a json file that list all the persons and the oranges that they do have'
    "echo \"Now let's see how to pipe tulp to tulp\""
    'tulp write a story about 3 persons, giving a name to each of them, they will find a bag with 10 oranges, 10 apples and 10 bananas, then they will share them | tulp write a python program that graph the fruits that each person using mathplotlib | python'
    'vim ../oranges_poem.txt'
)
