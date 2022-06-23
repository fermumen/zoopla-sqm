FROM gitpod/workspace-full 
ENV PYTHONUSERBASE=/workspace/.pip-modules
ENV PATH=$PYTHONUSERBASE/bin:$PATH
ENV PIP_USER=yes
RUN sudo apt-get update \
    &&  sudo apt install -y tesseract-ocr \
    &&  sudo apt install -y libtesseract-dev