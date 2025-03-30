#!/bin/bash

TAG="0.0.4"
#### Do not change below...
URL="https://github.com/eraby-fr/RegPaC/archive/refs/tags/${TAG}.zip"
TMP_DIR="/tmp"
ZIP_FILE="${TMP_DIR}/regpac.zip"
EXTRACT_DIR="${TMP_DIR}/RegPaC-${TAG}"
TARGET_DIR="$(pwd)/RegPaC"

echo -e "Welcome in fully automated deployement & run of RegPaC ${TAG}"
echo -e " "
echo -e "Starting process : RegPac will be deployed in the current folder."

echo -e "   Download files..."
wget -q -O "${ZIP_FILE}" "${URL}"
if [ $? -ne 0 ]; then
    echo "Fail to download ${URL}"
    exit 1
fi

echo -e "   Cleaning previous setup if needed"
rm -r "${EXTRACT_DIR}" "${TARGET_DIR}"  2> /dev/null

echo -e "   Unzipping files"
unzip -oq "${ZIP_FILE}" -d "${TMP_DIR}"
if [ $? -ne 0 ]; then
    echo "Fail to unzip ${ZIP_FILE}"
    exit 1
fi

echo -e "   Copy usefull files"
mkdir -p ${TARGET_DIR}
mv -f "${EXTRACT_DIR}/Deployement/Docker-Compose"/* "${TARGET_DIR}"/
if [ $? -ne 0 ]; then
    echo "Fail to move files."
    exit 1
fi

echo -e "   Cleaning temporary folders"
rm -rf "${ZIP_FILE}" "${EXTRACT_DIR}"
echo -e "End of 1st step deployement : success"
echo -e " "

echo -e "Starting 2nd step : retrieve docker images if needed"
echo -e " "
pushd "RegPaC"
docker compose -f regpac-compose.yml pull
if [ $? -ne 0 ]; then
    echo "Fail to retrieve docker images"
    exit 1
fi
echo -e "End of 2nd step deployement : success"
echo -e " "

echo -e "Start RegPac"
docker compose -f regpac-compose.yml up --remove-orphans

popd
echo -e " "

