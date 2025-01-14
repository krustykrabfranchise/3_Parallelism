import multiprocessing
from multiprocessing import Pool, Process, Queue, Lock
import random
import os
import time


def read_matrix(filename):
    with open(filename, 'r') as file:
        return [list(map(float, line.split())) for line in file if line.strip()]


def write_matrix(filename, matrix):
    with open(filename, 'w') as file:
        for row in matrix:
            file.write(' '.join(map(str, row)) + '\n')


def compute_element(args):
    i, j, A, B = args
    return i, j, sum(A[i][k] * B[k][j] for k in range(len(A[0])))


def multiply_matrices(A, B, num_processes=None):
    if len(A[0]) != len(B):
        raise ValueError("Количество столбцов первой матрицы должно совпадать с количеством строк второй.")
    tasks = [(i, j, A, B) for i in range(len(A)) for j in range(len(B[0]))]
    with Pool(processes=num_processes or multiprocessing.cpu_count()) as pool:
        results = pool.map(compute_element, tasks)
    result_matrix = [[0] * len(B[0]) for _ in range(len(A))]
    for i, j, value in results:
        result_matrix[i][j] = value
    return result_matrix


def generate_random_matrix(size):
    return [[random.uniform(0, 10) for _ in range(size)] for _ in range(size)]


def generate_matrix_process(size, queue, count, name):
    for _ in range(count):
        queue.put(generate_random_matrix(size))
        print(f"Сгенерирована матрица {name}.")
        time.sleep(0.1)
    queue.put(None)
    print(f"Генерация матриц {name} завершена.")


def async_multiply_matrices(queue_a, queue_b, result_queue):
    while True:
        A = queue_a.get()
        B = queue_b.get()
        if A is None or B is None:
            break
        result_queue.put(multiply_matrices(A, B))
        print("Перемножение матриц завершено.")
    result_queue.put(None)


if __name__ == "__main__":
    print("""
    Меню:
    1. Перемножение матриц из файлов
    2. Перемножение с промежуточной записью в файл
    3. Генерация случайных матриц и их асинхронное перемножение
    """)
    mode = input()

    match mode:
        case '1':
            file_a = input("Введите имя файла с первой матрицей: ")
            file_b = input("Введите имя файла со второй матрицей: ")
            result_file = input("Введите имя файла для сохранения результата: ")

            if not os.path.exists(file_a) or not os.path.exists(file_b):
                print("Один или оба файла не найдены.")
            else:
                A = read_matrix(file_a)
                B = read_matrix(file_b)
                result = multiply_matrices(A, B)
                write_matrix(result_file, result)
                print(f"Результат записан в файл {result_file}.")

        case '2':
            file_a = input("Введите имя и расширение файла с первой матрицей: ")
            file_b = input("Введите имя и расширение файла со второй матрицей: ")
            intermediate_file = input("Введите имя промежуточного файла: ")
            result_file = input("Введите имя файла для сохранения результата: ")

            if not os.path.exists(file_a) or not os.path.exists(file_b):
                print("Один или оба файла не найдены.")
            else:
                A = read_matrix(file_a)
                B = read_matrix(file_b)

                lock = Lock()
                rows, cols = len(A), len(B[0])
                tasks = [(i, j, A, B, lock, intermediate_file) for i in range(rows) for j in range(cols)]

                with open(intermediate_file, 'w'):  # Очистка промежуточного файла
                    pass
                with Pool(multiprocessing.cpu_count()) as pool:
                    pool.starmap(compute_element, tasks)

                result = multiply_matrices(A, B)
                write_matrix(result_file, result)
                print(f"Результат записан в файл {result_file}. Промежуточные данные сохранены в {intermediate_file}.")

        case '3':
            try:
                size = int(input("Введите размер матриц: "))
                count = int(input("Введите количество матриц: "))
            except ValueError:
                print("Некорректный ввод. Пожалуйста, введите числа.")
            else:
                queue_a = Queue()
                queue_b = Queue()
                result_queue = Queue()

                generator_a = Process(target=generate_matrix_process, args=(size, queue_a, count, 'A'))
                generator_b = Process(target=generate_matrix_process, args=(size, queue_b, count, 'B'))
                multiplier = Process(target=async_multiply_matrices, args=(queue_a, queue_b, result_queue))

                generator_a.start()
                generator_b.start()
                multiplier.start()

                completed = 0
                while True:
                    result = result_queue.get()
                    if result is None:
                        break
                    completed += 1
                    print(f"Результат перемножения матриц {completed} готов")

                generator_a.join()
                generator_b.join()
                multiplier.join()
                print(f"Перемножение {completed} пар матриц завершено.")

        case _:
            print("Некорректный ввод")
