# backend/services/geocoding_service.py
import re
import requests


def geocode_address(address_full):
    """
    Geocodifica um endereço brasileiro usando Nominatim (OpenStreetMap).

    Formato de entrada esperado:
    "Rua Nome, Número, Bairro, Cidade - Estado, CEP XXXXX-XXX, Brasil"

    O endereço é simplificado para melhor compatibilidade com Nominatim:
    - Remove prefixo "Rua/Av./Avenida/etc"
    - Remove o bairro
    - Mantém: "Nome da Rua, Número, Cidade, Brasil"

    Retorna (latitude, longitude) se encontrado, ou (None, None) se não encontrado.
    """
    if not address_full:
        return None, None

    try:
        # 1. Remover prefixo "Rua/Av./Avenida/Travessa/etc" e pegar nome da rua
        street_match = re.match(
            r'^(?:Rua|Av\.|Avenida|Travessa|Alameda|Praça)\s+([^,]+)',
            address_full,
            re.IGNORECASE
        )
        if street_match:
            street_name = street_match.group(1).strip()
        else:
            # Se não tem prefixo, pegar até a primeira vírgula
            street_name = address_full.split(',')[0].strip()

        # 2. Extrair número do endereço
        number_match = re.search(r',\s*(\d+)', address_full)
        number = number_match.group(1) if number_match else None

        # 3. Extrair cidade (antes do hífen com estado)
        city_match = re.search(r',\s*([^,]+)\s*-\s*([A-Z]{2})', address_full)
        city = city_match.group(1).strip() if city_match else None

        if not (street_name and city):
            print(f"❌ Não foi possível extrair rua ou cidade do endereço")
            return None, None

        # Montar endereço simplificado para Nominatim
        # Formato: "Nome da Rua, Número, Cidade, Brasil"
        if number:
            simplified_address = f"{street_name}, {number}, {city}, Brasil"
        else:
            simplified_address = f"{street_name}, {city}, Brasil"

        print(f"📍 Original: {address_full[:50]}...")
        print(f"   Simplificado: {simplified_address}")

        # Fazer requisição ao Nominatim
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": simplified_address,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        headers = {
            "User-Agent": "VenhaApp/1.0"
        }

        response = requests.get(url, params=params, headers=headers, timeout=3)
        response.raise_for_status()
        data = response.json()

        if data and len(data) > 0:
            result = data[0]
            lat = float(result.get("lat"))
            lon = float(result.get("lon"))

            if lat and lon and -90 <= lat <= 90 and -180 <= lon <= 180:
                print(f"   ✅ Sucesso! Lat={lat}, Lon={lon}")
                return lat, lon

        print(f"   ❌ Não encontrou coordenadas")
        return None, None

    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"❌ Erro ao geocodificar: {e}")
        return None, None
