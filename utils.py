import shutil

import docker
import tempfile
import os
import json

client = docker.from_env()

def run_code_in_docker(code, test_cases):
    # Создаем временный каталог для хранения файлов кода и тестов
    tmpdirname = tempfile.mkdtemp()
    try:
        # Создаем временный файл с пользовательским кодом
        solution_path = os.path.join(tmpdirname, 'solution.py')
        with open(solution_path, 'w') as solution_file:
            solution_file.write(code)

        # Создаем временный файл с тестами
        test_cases = json.loads(test_cases)
        runner_script = f"""
import json
import solution

test_cases = {json.dumps(test_cases)}

def run_tests():
    results = []
    for test in test_cases:
        function_name = test["function_name"]
        input_data = test["input"]
        expected_output = test["expected_output"]
        try:
            output = getattr(solution, function_name)(*input_data)
            passed = output == expected_output
        except Exception as e:
            output = str(e)
            passed = False
        results.append({{"input": input_data, "output": output, "expected": expected_output, "passed": passed}})
    return results

results = run_tests()
print(json.dumps(results))
"""
        runner_path = os.path.join(tmpdirname, 'runner.py')
        with open(runner_path, 'w') as runner_file:
            runner_file.write(runner_script)

        # Копируем файлы в контейнер и выполняем код
        try:
            result = client.containers.run(
                image="python:3",
                volumes={tmpdirname: {'bind': '/code', 'mode': 'rw'}},
                command="python /code/runner.py",
                working_dir="/code",
                remove=True
            )
            print("Result from Docker container:", result)  # Отладочный вывод
            return result.decode("utf-8")
        except docker.errors.ContainerError as e:
            return e.stderr.decode("utf-8")
    finally:
        # Удаляем временный каталог и его содержимое
        shutil.rmtree(tmpdirname, ignore_errors=True)
