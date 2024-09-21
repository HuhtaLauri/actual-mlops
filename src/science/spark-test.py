from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

DATA_PATH = "src/engineering/github/data/raw/commits/*/*/*"

df = spark.read.option("inferSchema", True).json(DATA_PATH)

print(df.show())
print(df.printSchema())

#df.select("commit.committer.date").show()
#df.createOrReplaceTempView("commits")
#tempres = spark.sql("SELECT commit FROM commits")

#print(tempres.show())
