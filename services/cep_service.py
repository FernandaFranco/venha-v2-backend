import requests


def get_address_from_cep(cep):
    """Look up address from Brazilian CEP using ViaCEP API"""

    # Clean CEP (remove dashes, spaces)
    cep_clean = cep.replace("-", "").replace(" ", "")

    if len(cep_clean) != 8:
        return None

    try:
        response = requests.get(f"https://viacep.com.br/ws/{cep_clean}/json/")

        if response.status_code == 200:
            data = response.json()

            # Check if CEP was found
            if "erro" in data:
                return None

            # Format full address
            address = f"{data['logradouro']}, {data['bairro']}, {data['localidade']} - {data['uf']}, {cep}"
            return address

        return None
    except Exception as e:
        print(f"CEP lookup error: {e}")
        return None
