def yes_no_input(prompt, return_bool=False):
    while True:
        response = input(prompt)
        if response == "yes" or response == "no":
            return response
        else:
            print("Veuillez entrer yes ou no")
    if return_bool:
        return response == "yes"
    return response


def ask_station(df_stops):
    while True:
        station = input("Entrer le nom de la station: ")
        if station in df_stops['stop_name'].values:
            return station
        else:
            print(f"La station {station} n'existe pas, veuillez réessayer")
            if yes_no_input("Voulez-vous réessayer? (yes/no): ") != "yes":
                return False
    return station


def select_networks():
    ter_network = yes_no_input(
        "Voulez-vous sélectionner le réseau TER? (yes/no): ", True)
    tgv_network = yes_no_input(
        "Voulez-vous sélectionner le réseau TGV? (yes/no): ", True)
    return ter_network, tgv_network
