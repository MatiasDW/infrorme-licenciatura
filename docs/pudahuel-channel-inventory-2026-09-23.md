# Inventario visible del canal de YouTube de Pudahuel

## Contexto

- Fuente: listado copiado desde la página pública del canal y adjuntado al proyecto el 23 de septiembre de 2026.
- Entradas visibles en el listado: 202.
- Cobertura observada: desde enero de 2016 hasta abril de 2026.
- El listado muestra duración, título, una métrica numérica y antigüedad relativa; no contiene los video_id.
- La métrica de cobertura visual no equivale a disponibilidad de transcript: debe validarse video por video.

## Reconciliación con la ingesta

La exploración automática actual encontró 741 videos con el filtro de sesiones/comisiones y 774 usando all_content=true. El listado adjunto es una referencia adicional para detectar diferencias de cobertura, especialmente en el archivo histórico 2016-2020. Para reconciliarlo de forma confiable se debe:

1. Descubrir nuevamente las pestañas videos y streams del canal.
2. Guardar todos los resultados por video_id, sin intentar transcript durante la fase de catálogo.
3. Comparar títulos y fechas aproximadas contra este inventario visual.
4. Intentar transcript en una cola separada, registrando available, blocked, not_found o unknown.

Los 718 pendientes actuales no representan necesariamente videos ausentes: están registrados en PostgreSQL, pero la descarga de transcript fue bloqueada por YouTube con HTTP 429.

## Listado original

<details>
<summary>Expandir las 202 entradas copiadas</summary>

~~~text
 
 1:45:02
 CUENTA PUBLICA 2025-2026 - 22 abril 2026.
 110
 hace 4 m
 
 
 1:25:40
 Copia de Reunión Ordinaria N°15 del Concejo Municipal, 17 de Mayo del 2023.
 784
 hace 3 a
 
 
 35:51
 Concejo Municipal, Reunión Extraordinaria N°18
 444
 hace 3 a
 
 
 1:25:03
 Concejo Municipal, Sesión Ordinaria N°29/2022
 330
 hace 3 a
 
 
 1:48:25
 Comisión de Finanzas, Concejo Municipal.
 173
 hace 4 a
 
 
 2:08:55
 Concejo Municipal, Sesión Extraordinaria N° 07/2022
 259
 hace 4 a
 
 
 1:50:21
 Concejo Municipal, Sesión Ordinaria N° 08/2022
 190
 hace 4 a
 
 
 43:18
 Cambio de Mando
 749
 hace 5 a
 
 
 58:13
 CUENTA PÚBLICA, GESTIÓN 2020
 1,1 K
 hace 5 a
 
 
 11:49
 Sesión Extraordinaria Nº 11/2021
 149
 hace 6 a
 
 
 13:35
 Sesión Extraordinaria Nº 10
 176
 hace 6 a
 
 
 1:17:44
 Sesión Extraordinaria Nº 9
 210
 hace 6 a
 
 
 3:26:28
 Sesión Ordinaria Nº 21
 361
 hace 6 a
 
 
 2:54:39
 Sesión Ordinaria N° 20
 241
 hace 6 a
 
 
 1:40:01
 Sesión Ordinaria Nº 19
 243
 hace 6 a
 
 
 2:09:52
 Sesión Extraordinaria Nº 8
 214
 hace 6 a
 
 
 2:39:22
 Sesión Ordinaria Nº 18
 171
 hace 6 a
 
 
 2:42:14
 Sesión Ordinaria Nº 17
 194
 hace 6 a
 
 
 1:19:12
 Sesión Extraordinaria Nº 7
 147
 hace 6 a
 
 
 2:41:02
 Sesión Ordinaria Nº 16
 105
 hace 6 a
 
 
 3:59:13
 Sesión Ordinaria Nº 15
 172
 hace 6 a
 
 
 1:17:37
 Sesión Extraordinaria Nº 6
 181
 hace 6 a
 
 
 3:17:21
 Sesión Extraordinaria Nº 5
 122
 hace 6 a
 
 
 1:33:20
 Sesión Ordinaria Nº 14
 100
 hace 6 a
 
 
 3:23:01
 Sesión Ordinaria Nº 13
 131
 hace 6 a
 
 
 41:33
 CUENTA PÚBLICA gestión 2019
 240
 hace 6 a
 
 
 3:17:47
 Sesión Ordinaria N° 12
 142
 hace 6 a
 
 
 3:50:07
 Sesión Ordinaria Nº 7
 162
 hace 6 a
 
 
 1:30:57
 Reunión Ordinaria Nº05 del Concejo Municipal, del día Miércoles 05 de Febrero del 2020.
 68
 hace 6 a
 
 
 2:07:40
 Reunión Ordinaria Nº06 del Concejo Municipal, del día Miércoles 07 de Febrero del 2020.
 78
 hace 6 a
 
 
 2:31:47
 Reunión Ordinaria Nº04 del Concejo Municipal, del día Miércoles 03 de Febrero del 2020.
 51
 hace 6 a
 
 
 3:34:55
 Reunión Ordinaria Nº03 del Concejo Municipal, del día Miércoles 22 de Enero del 2020.
 134
 hace 6 a
 
 
 3:12:32
 Reunión Ordinaria Nº02 del Concejo Municipal, del día Miércoles 15 de Enero del 2020.
 50
 hace 6 a
 
 
 1:33:57
 Reunión Extraordinaria Nº01 del Concejo Municipal, del día Miércoles 08 de Enero del 2020.
 140
 hace 6 a
 
 
 1:57:30
 Reunión Ordinaria Nº01 del Concejo Municipal, del día Miércoles 08 de Enero del 2020.
 86
 hace 6 a
 
 
 3:13:35
 Reunión Ordinaria Nº36 del Concejo Municipal, del día Miércoles 18 de Diciembre del 2019.
 132
 hace 6 a
 
 
 3:43:58
 Reunión Ordinaria Nº35 del Concejo Municipal, del día Miércoles 11 de Diciembre del 2019.
 76
 hace 6 a
 
 
 4:34:40
 Reunión Ordinaria Nº34 del Concejo Municipal, del día Miércoles 4 de Diciembre del 2019.
 216
 hace 6 a
 
 
 3:15
 PLADECO PUDAHUEL
 535
 hace 6 a
 
 
 3:23:14
 Reunión Ordinaria Nº29 del Concejo Municipal, del día Miércoles 08 de Octubre del 2019.
 254
 hace 6 a
 
 
 4:07:19
 Reunión Ordinaria Nº28 del Concejo Municipal, del día Miércoles 02 de Octubre del 2019.
 139
 hace 6 a
 
 
 4:51:55
 Reunión Ordinaria Nº27 del Concejo Municipal, del día Miércoles 25 de Septiembre del 2019.
 135
 hace 6 a
 
 
 2:21:50
 Reunión Extraordinaria Nº5 del Concejo Municipal, del día lunes 16 de Septiembre del 2019.
 109
 hace 6 a
 
 
 3:49:37
 Reunión Ordinaria Nº26 del Concejo Municipal, del día Miércoles 11 de Septiembre del 2019.
 200
 hace 6 a
 
 
 3:20:02
 Reunión Ordinaria Nº25 del Concejo Municipal, del día Miércoles 04 de Septiembre del 2019.
 265
 hace 7 a
 
 
 3:25:48
 Reunión Ordinaria Nº24 del Concejo Municipal, del día Miércoles 21 de Agosto del 2019.
 145
 hace 7 a
 
 
 3:53:33
 Reunión Ordinaria Nº23 del Concejo Municipal, del día Miércoles 14 de Agosto del 2019.
 123
 hace 7 a
 
 
 3:24:26
 Reunión Ordinaria Nº22 del Concejo Municipal, del día Miércoles 07 de Agosto del 2019.
 98
 hace 7 a
 
 
 1:40:46
 Reunión Extraordinaria Nº4 del Concejo Municipal, del día lunes 22 de Julio del 2019.
 270
 hace 7 a
 
 
 1:15:20
 Reunión Ordinaria Nº21 del Concejo Municipal, del día Miércoles 17 de Julio del 2019.
 100
 hace 7 a
 
 
 3:14:32
 Reunión Ordinaria Nº20 del Concejo Municipal, del día Miércoles 10 de Julio del 2019.
 136
 hace 7 a
 
 
 3:14:36
 Reunión Ordinaria Nº19 del Concejo Municipal, del día Miércoles 02 de Julio del 2019.
 143
 hace 7 a
 
 
 1:07:38
 Reunión Extraordinaria Nº3 del Concejo Municipal, del día Miércoles 26 de Junio del 2019.
 185
 hace 7 a
 
 
 3:32:16
 Reunión Ordinaria Nº18 del Concejo Municipal, del día Miércoles 19 de Junio del 2019.
 115
 hace 7 a
 
 
 3:03:05
 Reunión Ordinaria Nº17 del Concejo Municipal, del día Miércoles 12 de Junio del 2019.
 134
 hace 7 a
 
 
 1:46:23
 Reunión Extraordinaria Nº2 del Concejo Municipal, del día Miércoles 29 de Mayo del 2019.
 113
 hace 7 a
 
 
 2:23:38
 Reunión Ordinaria Nº15 del Concejo Municipal, del día Miércoles 22 de Mayo del 2019.
 129
 hace 7 a
 
 
 2:38:29
 Reunión Ordinaria Nº14 del Concejo Municipal, del día Miércoles 15 de Mayo del 2019.
 170
 hace 7 a
 
 
 3:50:30
 Reunión Ordinaria Nº13 del Concejo Municipal, del día Miércoles 08 de Mayo del 2019.
 110
 hace 7 a
 
 
 1:25:49
 Reunión Extraordinaria Nº1 del Concejo Municipal, del día Miércoles 24 de Abril del 2019.
 109
 hace 7 a
 
 
 3:51:33
 Reunión Ordinaria Nº12 del Concejo Municipal, del día Miércoles 17 de Abril del 2019.
 224
 hace 7 a
 
 
 2:21:08
 Reunión Ordinaria Nº11 del Concejo Municipal, del día Miércoles 10 de Abril del 2019.
 86
 hace 7 a
 
 
 3:49:33
 Reunión Ordinaria Nº10 del Concejo Municipal, del día Miércoles 03 de Abril del 2019.
 209
 hace 7 a
 
 
 3:21:14
 Reunión Ordinaria Nº09 del Concejo Municipal, del día Miércoles 20 de Marzo del 2019.
 304
 hace 7 a
 
 
 4:14:58
 Reunión Ordinaria Nº08 del Concejo Municipal, del día Miércoles 13 de Marzo del 2019.
 87
 hace 7 a
 
 
 1:45:07
 Reunión Ordinaria Nº07 del Concejo Municipal, del día Miércoles 06 de Marzo del 2019.
 37
 hace 7 a
 
 
 2:30:23
 Reunión Ordinaria Nº06 del Concejo Municipal, del día Viernes 08 de Febrero del 2019.
 77
 hace 7 a
 
 
 2:44:21
 Reunión Ordinaria Nº05 del Concejo Municipal, del día Miércoles 06 de Febrero del 2019.
 54
 hace 7 a
 
 
 2:18:22
 Reunión Ordinaria Nº04 del Concejo Municipal, del día lunes 04 de Febrero del 2019.
 71
 hace 7 a
 
 
 2:56:01
 Reunión Ordinaria Nº3 del Concejo Municipal, del día miércoles 19 de Enero del 2019.
 218
 hace 7 a
 
 
 2:53:07
 Sesión Ordinaria Nº02, del día miércoles 09 de Enero del 2019.
 124
 hace 7 a
 
 
 2:42:27
 Sesión Ordinaria Nº 01, del 03 de Enero de 2019.
 112
 hace 7 a
 
 
 3:18:35
 Sesión Extraordinaria Nº 8, del 26 de diciembre de 2018
 148
 hace 7 a
 
 
 2:12:15
 Sesión Ordinaria Nº 36, del 19 de diciembre de 2018
 73
 hace 7 a
 
 
 4:30:21
 Sesión Ordinaria Nº 35, del 12 de Diciembre de 2018
 367
 hace 7 a
 
 
 4:25:00
 Sesión Ordinaria Nº 34, del 5 de Diciembre de 2018
 213
 hace 7 a
 
 
 9:50
 Sesión Extraordinaria Nº 7, del 23 de Noviembre de 2018
 81
 hace 7 a
 
 
 4:26:57
 Sesión Ordinaria Nº 33, del 21 de Noviembre de 2018
 32
 hace 7 a
 
 
 2:59:17
 Sesión Ordinaria Nº 32, del 14 de Noviembre de 2018
 80
 hace 7 a
 
 
 3:54:03
 Sesión Ordinaria Nº 31, del 7 de Noviembre de 2018
 118
 hace 7 a
 
 
 2:46:25
 Sesión Extraordinaria Nº 6, del 24 de Octubre de 2018
 130
 hace 7 a
 
 
 2:29:49
 Sesión Ordinaria Nº 30, del 17 de Octubre de 2018
 45
 hace 7 a
 
 
 3:20:13
 Sesión Ordinaria Nº 29, del 10 de Octubre de 2018
 141
 hace 7 a
 
 
 3:37:10
 Sesión Ordinaria Nº 28, del 3 de Octubre de 2018
 141
 hace 7 a
 
 
 3:08:59
 Sesión Ordinaria Nº 26, del 12 de Septiembre de 2018
 63
 hace 7 a
 
 
 3:43:48
 Sesión Ordinaria Nº 25, del 5 de Septiembre de 2018
 32
 hace 8 a
 
 
 2:09:49
 Sesión Extraordinaria Nº 5, del 29 de Agosto de 2018
 39
 hace 8 a
 
 
 4:02:29
 Sesión Ordinaria Nº 24, del 22 de Agosto de 2018
 150
 hace 8 a
 
 
 3:47:12
 Sesión Ordinaria Nº 23, del 8 de Agosto de 2018
 333
 hace 8 a
 
 
 3:14:19
 Sesión Ordinaria Nº 22, del 1 de Agosto de 2018
 100
 hace 8 a
 
 
 2:33:18
 Sesión Ordinaria Nº 21, del 18 de Julio de 2018
 30
 hace 8 a
 
 
 3:16:24
 Sesión Ordinaria Nº 20, del 11 de Julio de 2018
 16
 hace 8 a
 
 
 3:23:15
 Sesión Ordinaria Nº 19, del 4 de Julio de 2018
 82
 hace 8 a
 
 
 1:47:24
 Sesión Ordinaria Nº 18, del 20 de Junio de 2018
 27
 hace 8 a
 
 
 2:56:34
 Sesión Ordinaria Nº 17, del 13 de Junio de 2018
 12
 hace 8 a
 
 
 2:46:53
 Sesión Ordinaria Nº 16, del 6 de Junio de 2018
 189
 hace 8 a
 
 
 2:47:47
 Sesión Extraordinaria Nº 3, del 23 de Mayo de 2018
 37
 hace 8 a
 
 
 2:59:38
 Sesión Ordinaria Nº 15, del 16 de Mayo de 2018
 67
 hace 8 a
 
 
 2:51:59
 Sesión Ordinaria Nº 14, del 9 de Mayo de 2018
 18
 hace 8 a
 
 
 2:11:23
 Sesión Ordinaria Nº 13, del 2 de Mayo de 2018
 43
 hace 8 a
 
 
 10:15
 Sesión Extraordinaria Nº 1, del 25 de Abril de 2018
 25
 hace 8 a
 
 
 48:00
 Sesión Ordinaria Nº 12, del 18 de Abril de 2018
 20
 hace 8 a
 
 
 1:33:33
 Cuenta Pública: Sesión Extraordinaria Nº 2, del 25 de Abril de 2018
 37
 hace 8 a
 
 
 3:11:51
 Sesión Ordinaria Nº 11, del 11 de Abril de 2018
 43
 hace 8 a
 
 
 2:53:41
 Sesión Ordinaria Nº 10, del 4 de Abril de 2018
 26
 hace 8 a
 
 
 1:06:03
 Sesión Ordinaria Nº 08, del 14 de Marzo de 2018
 119
 hace 8 a
 
 
 3:13:15
 Sesión Ordinaria Nº 07, del 7 de Marzo de 2018
 46
 hace 8 a
 
 
 3:24:29
 Sesión Ordinaria Nº 06, del 7 de Febrero de 2018
 37
 hace 8 a
 
 
 2:01:33
 Sesión Ordinaria Nº 05, del 5 de Febrero de 2018
 18
 hace 8 a
 
 
 2:22:39
 Sesión Ordinaria Nº 04, del 1 de Febrero de 2018
 26
 hace 8 a
 
 
 1:34:20
 Sesión Ordinaria Nº 03, del 17 de Enero de 2018
 76
 hace 8 a
 
 
 2:50:52
 Sesión Ordinaria Nº 02, del 10 de Enero de 2018
 22
 hace 8 a
 
 
 2:13:19
 Sesión Ordinaria Nº 01, del 3 de Enero de 2018
 17
 hace 8 a
 
 
 1:38:45
 Sesión Extraordinaria Nº 4, del 27 de Diciembre de 2017
 14
 hace 8 a
 
 
 3:25:47
 Sesión Ordinaria Nº 36, del 20 de Diciembre de 2017
 11
 hace 8 a
 
 
 3:55:12
 Sesión Ordinaria Nº 35, del 13 de Diciembre de 2017
 52
 hace 8 a
 
 
 2:39:34
 Sesión Ordinaria Nº 34, del 6 de Diciembre de 2017
 31
 hace 8 a
 
 
 3:16:19
 Sesión Ordinaria Nº 33, del 22 de Noviembre de 2017
 34
 hace 8 a
 
 
 3:34:27
 Sesión Ordinaria Nº 32, del 15 de Noviembre de 2017
 44
 hace 8 a
 
 
 4:24:51
 Sesión Ordinaria Nº 31, del 8 de Noviembre de 2017
 18
 hace 8 a
 
 
 3:24:55
 Sesión Ordinaria Nº 30, del 18 de Octubre de 2017
 20
 hace 8 a
 
 
 2:38:06
 Sesión Ordinaria Nº 29, del 11 de Octubre de 2017
 18
 hace 8 a
 
 
 3:09:05
 Sesión Ordinaria Nº 28, del 4 de Octubre de 2017
 52
 hace 8 a
 
 
 32:38
 Sesión Ordinaria Nº 27, del 20 de Septiembre de 2017
 13
 hace 8 a
 
 
 1:59:58
 Sesión Ordinaria Nº 26, del 13 de Septiembre de 2017
 15
 hace 8 a
 
 
 3:58:57
 Sesión Ordinaria Nº 25, del 6 de Septiembre de 2017
 14
 hace 8 a
 
 
 25:33
 Sesión Extraordinaria Nº 3, del 28 de Agosto de 2017
 12
 hace 8 a
 
 
 2:00:47
 Sesión Extraordinaria Nº 2, del 23 de Agosto de 2017
 77
 hace 9 a
 
 
 1:38:28
 Sesión Ordinaria Nº 24, del 16 de Agosto de 2017
 43
 hace 9 a
 
 
 2:56:42
 Sesión Ordinaria Nº 23, del 9 de Agosto de 2017
 30
 hace 9 a
 
 
 2:39:47
 Sesión Ordinaria Nº 22, del 2 de Agosto de 2017
 54
 hace 9 a
 
 
 1:21:58
 Sesión Ordinaria Nº 21, del 19 de Julio de 2017
 57
 hace 9 a
 
 
 1:41:53
 Audiencia Pública N° 1 del 10 de Julio de 2017
 202
 hace 9 a
 
 
 3:20:41
 Sesión Ordinaria Nº 20, del 12 de Julio de 2017
 50
 hace 9 a
 
 
 3:06:58
 Sesión Ordinaria Nº 19, del 5 de Julio de 2017
 49
 hace 9 a
 
 
 2:09:59
 Sesión Ordinaria Nº 18, del 21 de Junio de 2017
 46
 hace 9 a
 
 
 2:59:05
 Sesión Ordinaria Nº 17, del 14 de Junio de 2017
 45
 hace 9 a
 
 
 2:04:56
 Sesión Ordinaria Nº 16, del 7 de Junio de 2017
 45
 hace 9 a
 
 
 4:02:54
 Sesión Ordinaria Nº 15, del 17 de Mayo de 2017
 140
 hace 9 a
 
 
 2:57:58
 Sesión Ordinaria Nº 14, del 10 de Mayo de 2017
 133
 hace 9 a
 
 
 1:39:57
 Sesión Ordinaria Nº 13, del 5 de Mayo de 2017
 60
 hace 9 a
 
 
 1:45:56
 Sesión Extraordinaria Nº 1, del 26 de Abril de 2017, Cuenta Pública
 90
 hace 9 a
 
 
 2:31:36
 Sesión Ordinaria Nº 12, del 21 de Abril de 2017
 98
 hace 9 a
 
 
 3:58:07
 Sesión Ordinaria Nº 11, del 12 de Abril de 2017
 669
 hace 9 a
 
 
 3:35:28
 Sesión Ordinaria Nº 10, del 5 de Abril de 2017
 38
 hace 9 a
 
 
 3:28:10
 Sesión Ordinaria Nº 9, del 15 de Marzo de 2017
 41
 hace 9 a
 
 
 2:11:43
 Sesión Ordinaria Nº 8, del 8 de Marzo de 2017
 27
 hace 9 a
 
 
 1:55:28
 Sesión Ordinaria Nº 7, del 1 de Marzo de 2017
 36
 hace 9 a
 
 
 3:44:40
 Sesión Ordinaria Nº 6, del 6 de Febrero de 2017
 17
 hace 9 a
 
 
 1:57:36
 Sesión Ordinaria Nº 5, del 3 de Febrero de 2017
 19
 hace 9 a
 
 
 2:23:40
 Sesión Ordinaria Nº 4, del 1 de Febrero de 2017
 14
 hace 9 a
 
 
 3:24:12
 Sesión Ordinaria Nº 3, del 18 de Enero de 2017
 38
 hace 9 a
 
 
 4:30:08
 Sesión Ordinaria Nº 2, del 11 de Enero de 2017
 41
 hace 9 a
 
 
 1:18:05
 Sesión Ordinaria Nº 1, del 4 de Enero de 2017
 25
 hace 9 a
 
 
 37:27
 Sesión Extraordinaria Nº 1, del 28 de Diciembre de 2016
 21
 hace 9 a
 
 
 3:27:42
 Sesión Ordinaria Nº 3, del 21 de iembre de 2016
 25
 hace 9 a
 
 
 2:05:54
 Sesión Ordinaria Nº 2, del 14 de iembre de 2016
 22
 hace 9 a
 
 
 1:13:49
 Sesión Ordinaria Nº 1, del 7 de Diciembre de 2016
 123
 hace 9 a
 
 
 3:08:08
 Sesión Extraordinaria Nº 14, del 16 de Noviembre de 2016
 18
 hace 9 a
 
 
 1:19:31
 Sesión Ordinaria Nº 32, del 2 de Noviembre de 2016 2
 12
 hace 9 a
 
 
 25:17
 Sesión Extraordinaria Nº 13, del 26 de Octubre de 2016
 11
 hace 9 a
 
 
 2:08:49
 Sesión Ordinaria Nº 31, del 19 de Octubre de 2016
 21
 hace 9 a
 
 
 1:39:00
 Sesión Ordinaria Nº 30, del 12 de Octubre de 2016
 19
 hace 9 a
 
 
 2:19:07
 Sesión Ordinaria Nº 29, del 5 de Octubre de 2016
 28
 hace 9 a
 
 
 2:47:31
 Sesión Ordinaria Nº 28, del 21 de Septiembre de 2016
 5
 hace 9 a
 
 
 1:43:33
 Sesión Extraordinaria Nº 12, del 28 de Septiembre de 2016
 13
 hace 9 a
 
 
 3:02:21
 Sesión Ordinaria Nº 27, del 14 de Septiembre de 2016
 14
 hace 9 a
 
 
 2:25:36
 Sesión Ordinaria Nº 26, del 7 de Septiembre de 2016
 14
 hace 9 a
 
 
 1:34:50
 Sesión Extraordinaria Nº 11, del 31 de Agosto de 2016
 6
 hace 9 a
 
 
 2:02:32
 Sesión Extraordinaria Nº 10, del 24 de Agosto de 2016
 7
 hace 9 a
 
 
 3:18:48
 Sesión Ordinaria Nº 25, del 17 de Agosto de 2016
 6
 hace 9 a
 
 
 3:27:34
 Sesión Ordinaria Nº 24, del 10 de Agosto de 2016
 18
 hace 10 a
 
 
 1:39:32
 Sesión Ordinaria Nº 23, del 3 de Agosto de 2016
 6
 hace 10 a
 
 
 2:29:12
 Sesión Extraordinaria Nº 9, del 27 de Julio de 2016
 8
 hace 10 a
 
 
 38:09
 Sesión Ordinaria Nº 21, del 13 de Julio de 2016
 5
 hace 10 a
 
 
 1:56:48
 Sesión Ordinaria Nº 20, del 6 de Julio de 2016
 4
 hace 10 a
 
 
 35:06
 Sesión Extraordinaria Nº 7, del 22 de Junio de 2016
 16
 hace 10 a
 
 
 1:24:44
 Sesión Ordinaria Nº 19, del 15 de Junio de 2016
 10
 hace 10 a
 
 
 2:22:55
 Sesión Ordinaria Nº 17, del 1 de Junio de 2016
 13
 hace 10 a
 
 
 20:28
 Sesión Ordinaria Nº 18, del 8 de Junio de 2016
 15
 hace 10 a
 
 
 2:31:45
 Sesión Extraordinaria Nº 6, del 25 de Mayo de 2016
 9
 hace 10 a
 
 
 17:11
 Sesión Ordinaria Nº 16, del 18 de Mayo de 2016
 22
 hace 10 a
 
 
 2:28:51
 Sesión Ordinaria Nº 15, del 11 de Mayo de 2016
 107
 hace 10 a
 
 
 2:30:11
 Sesión Ordinaria Nº 14, del 4 de Mayo de 2016
 10
 hace 10 a
 
 
 1:18:38
 Sesión Extraordinaria Nº 5, del 27 de Abril de 2016, Cuenta Pública año 2015
 14
 hace 10 a
 
 
 2:15:03
 Sesión Extraordinaria Nº 4, del 27 de Abril de 2016
 21
 hace 10 a
 
 
 3:05:32
 Sesión Ordinaria Nº 12, del 13 de Abril de 2016
 11
 hace 10 a
 
 
 1:48:17
 Sesión Ordinaria Nº 13, del 20 de Abril de 2016
 18
 hace 10 a
 
 
 2:22:33
 Sesión Ordinaria Nº 11, del 6 de Abril de 2016
 12
 hace 10 a
 
 
 2:47:53
 Sesión Ordinaria Nº 10, del 23 de Marzo de 2016
 10
 hace 10 a
 
 
 2:23:16
 Sesión Extraordinaria Nº 3, del 30 de Marzo de 2016
 22
 hace 10 a
 
 
 1:36:23
 Sesión Ordinaria Nº 9, del 16 de Marzo de 2016
 16
 hace 10 a
 
 
 1:57:03
 Sesión Ordinaria Nº 6, del 5 de Febrero de 2016
 9
 hace 10 a
 
 
 2:57:45
 Sesión Ordinaria Nº 5, del 3 de Febrero de 2016
 13
 hace 10 a
 
 
 40:48
 Sesión Ordinaria Nº 8, del 9 de Marzo de 2016
 26
 hace 10 a
 
 
 29:29
 Sesión Ordinaria Nº 7, del 2 de Marzo de 2016
 7
 hace 10 a
 
 
 2:07:31
 Sesión Ordinaria Nº 4, del 1 de Febrero de 2016
 8
 hace 10 a
 
 
 1:02:52
 Sesión Extraordinaria Nº 1, del 27 de Enero de 2016
 9
 hace 10 a
 
 
 1:51:03
 Sesión Ordinaria Nº 3, del 20 de Enero de 2016
 14
 hace 10 a
 
 
 2:01:53
 Sesión Ordinaria Nº 2, del 13 de Enero de 2016
 20
 hace 10 a
 
 
 1:56:25
 Sesión Ordinaria Nº 1, del 6 de Enero de 2016
 41
 hace 10 a
 
 
 43:31
 Sesión Extraordinaria Nº 2, del 9 de Marzo de 2016
 74
 hace 10 a
~~~

</details>
