<template>
    <div v-if="isAuth(['ROOT', 'PERMISSION:SELECT'])">
        <el-table :data="dataList" border v-loading="dataListLoading" :cell-style="{ padding: '3px 0' }" style="width: 100%;" row-key="id" :tree-props="{ children: 'children' }">
            <el-table-column type="index" header-align="center" align="center" width="100" label="序号">
                <template #default="scope">
                    <span>{{ scope.$index + 1 }}</span>
                </template>
            </el-table-column>
            <el-table-column prop="permissionName" header-align="center" align="center" min-width="200" label="权限名称" />
            <el-table-column prop="moduleName" header-align="center" align="center" min-width="150" label="所属模块" />
            <el-table-column prop="actionName" header-align="center" align="center" min-width="150" label="操作类型" />
        </el-table>
    </div>
</template>

<script>
export default {
    data: function() {
        return {
            dataList: [],
            dataListLoading: false
        };
    },
    methods: {
        loadDataList: function() {
            let that = this;
            that.dataListLoading = true;
            that.$http('permission/selectAllPermissions', 'GET', null, true, function(resp) {
                that.dataList = resp.result;
                that.dataListLoading = false;
            });
        }
    },
    created: function() {
        this.loadDataList();
    }
};
</script>

<style></style>
VUEEOF; __tr_native_ec=$?; pwd -P >| '/var/folders/hn/1ylcxx294sz85pbtym3z3h880000gn/T/agent-toolhost/jobs/job-cddc948a9d5942b5957a297ff9d66039/cwd.txt'; exit "$__tr_native_ec"