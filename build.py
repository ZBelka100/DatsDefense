import requests
import json
import time

def comp(a):
    return (a['x'], a['y'])

def dist(x, y, b_x, b_y):
    dist = (x - b_x)**2 + (y - b_y)**2 
    return dist

world_url = "https://games.datsteam.dev/play/zombidef/world"
zombie_url = "https://games.datsteam.dev/play/zombidef/units"
command_url = "https://games.datsteam.dev/play/zombidef/command"
token = ""

headers = {
    "Content-Type": "application/json",
    "X-Auth-Token": token
}

while True:
    world_response = requests.get(world_url, headers=headers)
    zombie_response = requests.get(zombie_url, headers=headers)


    world_data = world_response.json()
    zombie_data = zombie_response.json()

    bases = zombie_data.get('base', [])
    zombies = zombie_data.get('zombies', [])
    enemy = zombie_data.get('enemyBlocks', [])

    # в случае невалидных данных с сервера
    if zombies is None:
        zombies = []

    if enemy is None:
        enemy = []

    if bases is None:
        bases = []
    

    gx = 0
    gy = 0

    #Сортировка врагов по удаленности от центра базы
    enemy.sort(key=lambda z: dist(gx, gy, z['x'], z['y']))
    zombies.sort(key=lambda z: dist(gx, gy, z['x'], z['y']))
    #Наоборот
    bases.sort(key=lambda z: dist(gx, gy, z['x'], z['y']), reverse=True)

    #zombie_spawn_points = set((z['x'], z['y']) for z in world_data.get('zpots', []))
    #walls = set((w['x'], w['y']) for w in world_data.get('walls', []))


    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    build = []
    attack_t = []

    for base in bases:
        haveTarget = False
        id = base['id']
        b_x = base['x']
        b_y = base['y']
        if (base['range'] == 8):
            gx = b_x
            gy = b_y

        for zombie in zombies:
            x = zombie['x']
            y = zombie['y']                
        
            if dist(x, y, b_x, b_y) <= base['range']*base['range'] and zombie['health'] > 0:
                attack_t.append({"blockId": id,"target": {"x": x,"y": y}})
                zombie['health'] -= base['attack']
                haveTarget = True #чтобы после выбора цели сразу переходили к попытке построить
                break

        for enemy_block in enemy:
            if haveTarget:
                break
            x = enemy_block['x']
            y = enemy_block['y']

            if dist(x, y, b_x, b_y) <= base['range']*base['range'] and enemy_block['health'] > 0:
                attack_t.append({"blockId" : id, "target" : {"x": x,"y": y} })
                enemy_block['health'] -= base['attack']
                haveTarget = True
                break

        
        if haveTarget: #гениальная оптимизация - если нет врагов, то скорее всего башня в центре, включать эту оптимизацию после n-го хода
            for dir in directions:
                build.append({"x": base['x'] + dir[0], "y": base['y'] + dir[1]})


    payload = {
        'build': build,
        'attack' : attack_t
    }
    count_moves = 0

    #отправка команды на действия
    response = requests.post(command_url, headers=headers, json=payload)

    formatted_world_response = json.dumps(world_response.json(), indent=4, ensure_ascii=False)
    formatted_zombie_response = json.dumps(zombie_response.json(), indent=4, ensure_ascii=False)

    #Таймер для того, чтобы получать актуальную инфу
    wait_time = zombie_data['turnEndsInMs'] * 0.001
    time.sleep(wait_time)
    
    print(formatted_zombie_response)

    