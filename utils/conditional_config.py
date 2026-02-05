import copy, yaml

class ConditionalConfig:
    @staticmethod
    def parse(config, env):
        # print(yaml.dump(env, sort_keys=False))
        return ConditionalConfig._prune(config, env)
    
    @staticmethod
    def _prune(node, env):
        # Case 1: list -> rebuild list, flatten sublists
        if isinstance(node, list):
            new_list = []
            for item in node:
                pruned = ConditionalConfig._prune(item, env)

                if pruned is None:
                    continue

                # If a dict turned into a list via "do:", flatten it here
                if isinstance(pruned, list):
                    new_list.extend(pruned)
                else:
                    new_list.append(pruned)

            return new_list

        # Case 2: dict -> evaluate when:, then handle do:, then recurse
        if isinstance(node, dict):
            # 1. Handle when:
            if "when" in node:
                if not ConditionalConfig._evaluate_condition(node["when"], env):
                    return None
                node = {k: v for k, v in node.items() if k != "when"}

            # 2. If dict contains "do", flatten it by returning the list directly
            if "do" in node:
                if "sudo" in node and node["sudo"] == True:
                    for item in node["do"]:
                        if isinstance(item, dict):
                            item["sudo"] = True

                pruned_do = ConditionalConfig._prune(node["do"], env)
                return pruned_do  # may be list or None

            # 3. Normal dict recursion
            new_dict = {}
            for k, v in node.items():
                pruned = ConditionalConfig._prune(v, env)
                if pruned is not None:
                    new_dict[k] = pruned
            return new_dict

        # Case 3: scalar
        return node

    @staticmethod
    def _evaluate_condition(conditions, env):
        if isinstance(conditions, dict):
            conditions = [conditions]

        for condition in conditions:
            for key, value in condition.items():
                if key == "not":
                    if ConditionalConfig._evaluate_condition(value, env):
                        return False
                elif key in ["or", "any", "either"]:
                    for subcond in value:
                        if ConditionalConfig._evaluate_condition([subcond], env):
                            break
                    else:
                        return False
                elif key == "tag":
                    if value not in env.get("tags", []):
                        return False
                elif env.get(key) != value:
                    return False
        return True