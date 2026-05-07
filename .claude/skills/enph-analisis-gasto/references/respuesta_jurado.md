# Cómo estructurar una respuesta a observaciones del jurado

Cuando la tarea no es producir un capítulo nuevo sino responder a observaciones específicas que el jurado hizo a un borrador de tesis, el formato cambia. La estructura típica es una **carta o documento de respuesta** que acompaña al manuscrito revisado.

## Principios

1. **Responder a cada observación punto por punto**, en el mismo orden y con la misma numeración que usó el jurado.
2. **Reconocer la observación con respeto**, sin defensa excesiva ni adulación.
3. **Mostrar la respuesta concretamente**: qué se cambió, dónde está en el manuscrito, qué evidencia adicional se agregó.
4. **Si no se aceptó la sugerencia, explicar por qué con argumento técnico**, no con evasivas.

## Estructura del documento de respuesta

```
Respuesta a observaciones del jurado evaluador
Tesis: [título de la tesis]
Autora: [nombre]
Fecha: [fecha]

Estimado(a) profesor(a) [nombre]:

Agradezco las observaciones detalladas a la versión preliminar de la tesis.
A continuación, respondo a cada punto. Las modificaciones realizadas en el
manuscrito se identifican con cambios resaltados en amarillo en la versión
revisada que se anexa.

---

OBSERVACIÓN 1
[Cita textual de la observación del jurado, en cursiva o entre comillas]

Respuesta:
[Reconocimiento breve de la observación.]
[Descripción concreta de qué se hizo: nuevo análisis, nueva tabla, cambio
en la redacción, sección añadida.]
[Referencia explícita a la página y/o sección del manuscrito revisado donde
se ve el cambio.]
[Si aplica: nuevo resultado o número que sustenta la respuesta.]

---

OBSERVACIÓN 2
[...]
```

## Patrones de respuesta efectivos

### Patrón A: "Aceptación con implementación"
> "Se acepta la observación. Para responder a esta inquietud se realizó [análisis específico] y los resultados se reportan en la nueva Tabla X (página Y) y en el Anexo Z. La principal conclusión es [resultado]. Esto refuerza/matiza el resultado original al mostrar que [interpretación]."

### Patrón B: "Aceptación parcial con nueva evidencia"
> "Se acepta parcialmente la observación. [Reconocimiento del punto válido]. Sin embargo, [argumento técnico para mantener parte del enfoque original]. Para abordar la preocupación, se agregó [análisis complementario] cuyos resultados se presentan en [ubicación]."

### Patrón C: "No aceptación con argumento"
> "Se entiende la inquietud del/la profesor(a), pero se considera que [decisión metodológica original] sigue siendo apropiada porque [argumento técnico, idealmente con cita]. Adicionalmente, [robustez que apoya la decisión]. Aun así, en el Anexo X se reporta el resultado bajo la especificación alternativa sugerida, donde se observa que [resultado] — esto confirma que las conclusiones principales son robustas."

## Errores frecuentes que evitar

- **No reconocer la observación**: ir directamente a la defensa parece arrogante.
- **Aceptar todo sin discutir**: a veces el jurado sugiere algo que no aplica al caso; explicarlo es señal de dominio del tema.
- **Cambiar de tema**: responder a una observación sobre supuestos hablando de los resultados es evasivo.
- **No mostrar dónde se hizo el cambio**: el jurado va a buscar el cambio en el manuscrito; debes facilitarle la localización.
- **Tono defensivo**: "No estoy de acuerdo con esta crítica porque..." → mejor: "Se considera importante mantener este enfoque porque..."

## Tipos comunes de observación y cómo abordarlos

### "Falta justificar la elección del método X"
- Agregar párrafo metodológico con cita de literatura.
- Si es posible, ejecutar también el método alternativo y comparar.

### "Los resultados pueden estar sesgados por endogeneidad/selección/etc."
- Reconocer la limitación.
- Implementar al menos una corrección (Heckman, IV, etc.) o al menos una prueba que sugiera la robustez.
- Si no es posible corregirlo, declararlo explícitamente como limitación.

### "Falta robustez a [especificación alternativa]"
- Es la más fácil: ejecutar la alternativa y reportar en una tabla nueva.
- Discutir si los hallazgos cualitativos cambian.

### "Los clusters no son interpretables / faltan pruebas para K-means"
- Agregar criterios de selección de K (silhouette, elbow, Calinski-Harabasz).
- Tabular características medias por cluster.
- Asignar nombres descriptivos a cada cluster.
- Considerar comparar con clustering jerárquico.

### "Falta conexión con literatura colombiana / latinoamericana"
- Buscar y citar 3-5 trabajos pertinentes (Núñez, Sánchez, Lasso, Galvis, etc., que han trabajado gasto y desigualdad en Colombia).
- Incorporar sus hallazgos en la sección de discusión.

## Formato del documento entregable

Si se entrega como `.docx`:
- Título del documento.
- Encabezado con datos de la tesis.
- Cada observación numerada y en cursiva o sombreado para distinguirla de la respuesta.
- Respuesta en texto normal.
- Páginas numeradas.
- Si hay tablas o gráficos nuevos, incluirlos en el cuerpo o en anexo según extensión.
