FROM continuumio/anaconda3
WORKDIR /quanten
ADD . /quanten
RUN apt-get update
RUN apt-get install -y build-essential
RUN apt-get -y install gcc
RUN pip install -r requirements.txt
ENV NETSIM /quanten/SimulaQron
ENV PYTHONPATH /quanten:/quanten/tinyIpcLib
CMD ["/bin/bash"]