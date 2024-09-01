# Método de Benders Lógico para o 2D-BPP

Este projeto implementa uma decomposição lógica de Benders para o problema conhecido como  *Two-Dimensional Bin Packing Problem* (2D-BPP). Experimentos com instâncias da literatura foram conduzidos. As instâncias e resultados estão compactadas no arquivo *experiments_august_2024*. [Este relatório](benders_para_2d-bpp.pdf) descreve o problema e a modelagem realizada, assim como os experimentos realizados e os resultados obtidos. 

## Execução do código-fonte

### Execução de um instância

Para a execução de uma intância, utilize o comando a seguir:

```python3 main.py <nome-instancia> <diretório-de-saída> <código-método>```,

sendo <nome-da-instância\> nome da instância a ser executada, <diretório-de-saída\> o local onde devem ser salvos os resultados da execução, e <código-método\> o código do método a ser utilizado. Se o código passado tenha valor 1, será executada a decomposição de Benders proposta. Se for diferente de 1 ou se não for passado um valor, será executado o modelo padrão descrito no relatório.

### Execução de várias instâncias

Para a execução de várias instâncias utilize o comando a seguir:
 
```python3 run_experiments.py <diretorio-com-entradas> <diretório-das-saídas>```,

sendo <diretorio-com-entradas\> o diretório onde se localiza todas as instâncias a serem executadas, e <diretório-das-saídas\> o diretório onde a saída de cada instância deve ser salva. Um detalhe importante, é que este comando irá executar ambos os métodos implementados: o modelo padrão descrito no relatório e a decomposição de benders.

## Reprodução dos experimentos do relatório

Para reproduzir a execução dos experimentos do relatório, utilize o comando para execução de várias instâncias utilizando o diretório [*instances_experiments*](instances_experiments/) como entrada.

Garanta que a variável *time_limit*, declarada na função *run* do arquivo [main.py](main.py), tenha valor igual a 1800. Assim, o tempo limite será de 30 minutos, como no relatório.

## Autores

[Arthur H. S. Cruz](https://github.com/thuzax/) ([ver currículo Lattes](http://lattes.cnpq.br/7792617711548023))

Walison Adrian de Oliveira([ver currículo Lattes](http://lattes.cnpq.br/5950090124404335))