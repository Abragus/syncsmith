def get_os_release(path="/etc/os-release"):
    data = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            # Remove surrounding quotes if present
            value = value.strip().strip('"').strip("'")
            data[key] = value
    return data