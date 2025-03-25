pragma foreing_kyes=ON;
Begin transaction;
CREATE TABLE IF NOT EXISTS quotes (
id INTEGER PRIMARY KEY AUTOINCREMENT,
author TEXT NOT NULL,
text TEXT NOT NULL
);
INSERT INTO
quotes (author,text)
VALUES
('Rick Cook', 'Программирование сегодня — это гонка
разработчиков программ, стремящихся писать программы с
большей и лучшей идиотоустойчивостью, и вселенной, которая
пытается создать больше отборных идиотов. Пока вселенная
побеждает.'),
('Waldi Ravens', 'Программирование на С похоже на быстрые танцы
на только что отполированном полу людей с острыми бритвами в
руках.'),
('Mosher’s Law of Software Engineering', 'Не волнуйтесь, 
если что-то не работает. Если
бы всё работало, вас бы уволили.'),
('Yoggi Berra', 'В теории, теория и практика неразделимы. На
практике это не так.')
;
commit;